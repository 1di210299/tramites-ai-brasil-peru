#!/usr/bin/env python3
"""
Scraper especializado para URLs específicas de TUPA
Procesa los enlaces importantes proporcionados por el usuario
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import json
import os
from datetime import datetime

from tupa_scraper import ProcedureData

logger = logging.getLogger(__name__)

class SpecializedScraper:
    """Scraper especializado para URLs específicas"""
    
    def __init__(self, links_file: str = None):
        self.session = None
        self.links_file = links_file or '../../../docs/links.txt'
        self.specialized_extractors = {
            'sunat.gob.pe': self._extract_sunat_procedure,
            'gob.pe': self._extract_gob_procedure,
            'reniec.gob.pe': self._extract_reniec_procedure,
            'mtc.gob.pe': self._extract_mtc_procedure
        }
        
        # Patrones específicos para cada entidad
        self.sunat_patterns = {
            'codigo_pattern': re.compile(r'(?:Código|N°|PROCEDIMIENTO)\s*[:.\-\s]*([A-Z0-9\-\.]+)', re.IGNORECASE),
            'tasa_pattern': re.compile(r'(?:Tasa|Derecho|Arancel)\s*[:.\-\s]*S/\.?\s*(\d+(?:\.\d{2})?)', re.IGNORECASE),
            'uit_pattern': re.compile(r'(\d+(?:\.\d{2})?)\s*%?\s*UIT', re.IGNORECASE),
            'plazo_pattern': re.compile(r'(?:Plazo|Tiempo)\s*[:.\-\s]*(\d+)\s*(día|días|hábil|hábiles)', re.IGNORECASE)
        }

    async def setup_session(self):
        """Configurar sesión HTTP"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-PE,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)

    def load_target_urls(self) -> List[str]:
        """Cargar URLs objetivo desde archivo"""
        urls = []
        
        try:
            # Intentar cargar desde el archivo de links
            if os.path.exists(self.links_file):
                with open(self.links_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('http'):
                            urls.append(line)
            else:
                logger.warning(f"Archivo {self.links_file} no encontrado")
                
        except Exception as e:
            logger.error(f"Error cargando URLs: {e}")
        
        # URLs de fallback si no se puede cargar el archivo
        if not urls:
            urls = [
                'https://www.gob.pe/250-renovar-dni-para-mayores-de-edad',
                'https://www.gob.pe/226-duplicado-de-dni-electronico-dnie',
                'https://tupadigital.mtc.gob.pe/#/inicio'
            ]
        
        return urls

    async def scrape_specialized_urls(self) -> List[ProcedureData]:
        """Scraper principal para URLs especializadas"""
        await self.setup_session()
        
        urls = self.load_target_urls()
        logger.info(f"Procesando {len(urls)} URLs especializadas")
        
        procedures = []
        
        for i, url in enumerate(urls):
            try:
                logger.info(f"Procesando {i+1}/{len(urls)}: {url}")
                
                procedure = await self._scrape_specialized_url(url)
                if procedure:
                    procedures.append(procedure)
                    logger.info(f"✅ Extraído: {procedure.name}")
                else:
                    logger.warning(f"⚠️ No se pudo extraer información de: {url}")
                
                # Delay entre requests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error procesando {url}: {e}")
                continue
        
        await self.session.close()
        return procedures

    async def _scrape_specialized_url(self, url: str) -> Optional[ProcedureData]:
        """Scraper para URL individual con extractores especializados"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} para {url}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Determinar extractor según dominio
                domain = urlparse(url).netloc
                
                extractor = None
                for domain_key, extractor_func in self.specialized_extractors.items():
                    if domain_key in domain:
                        extractor = extractor_func
                        break
                
                if extractor:
                    return await extractor(soup, url)
                else:
                    # Extractor genérico
                    return await self._extract_generic_procedure(soup, url)
                    
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    async def _extract_sunat_procedure(self, soup: BeautifulSoup, url: str) -> Optional[ProcedureData]:
        """Extractor especializado para SUNAT"""
        try:
            # Título del procedimiento
            title_selectors = ['h1', 'h2', '.titulo', '.procedimiento-titulo']
            name = self._extract_text_by_selectors(soup, title_selectors)
            
            if not name:
                # Extraer de URL si no hay título claro
                path_parts = url.split('/')
                if 'despa-pg' in url:
                    name = f"Procedimiento Aduanero {path_parts[-1].replace('.htm', '').replace('despa-pg.', 'PG-')}"
                else:
                    name = "Procedimiento SUNAT"
            
            # Descripción
            desc_selectors = ['.descripcion', '.contenido', '.resumen', 'p']
            description = self._extract_text_by_selectors(soup, desc_selectors, max_length=500)
            
            # Código TUPA
            text_content = soup.get_text()
            codigo_match = self.sunat_patterns['codigo_pattern'].search(text_content)
            tupa_code = codigo_match.group(1) if codigo_match else self._generate_code_from_url(url)
            
            # Costos
            cost = 0.0
            currency = "PEN"
            
            # Buscar tasas en UIT
            uit_match = self.sunat_patterns['uit_pattern'].search(text_content)
            if uit_match:
                uit_value = float(uit_match.group(1))
                # UIT 2024 = S/ 5,150
                cost = uit_value * 5150 / 100 if uit_value < 1 else uit_value * 5150
            else:
                # Buscar tasa directa
                tasa_match = self.sunat_patterns['tasa_pattern'].search(text_content)
                if tasa_match:
                    cost = float(tasa_match.group(1))
            
            # Tiempo de procesamiento
            plazo_match = self.sunat_patterns['plazo_pattern'].search(text_content)
            processing_time = plazo_match.group(0) if plazo_match else "No especificado"
            
            # Requisitos (buscar listas y párrafos con requisitos)
            requirements = self._extract_requirements_sunat(soup)
            
            # Base legal
            legal_basis = self._extract_legal_references(soup)
            
            # Categorización específica para SUNAT
            category = self._categorize_sunat_procedure(name, description, url)
            
            return ProcedureData(
                name=name,
                description=description,
                entity_name="SUNAT",
                entity_code="SUNAT",
                tupa_code=tupa_code,
                requirements=requirements,
                cost=cost,
                currency=currency,
                processing_time=processing_time,
                legal_basis=legal_basis,
                channels=["Presencial", "Virtual"],
                category=category,
                subcategory=self._get_sunat_subcategory(url),
                is_free=cost == 0,
                is_online=True,
                difficulty_level=self._assess_difficulty_sunat(requirements, cost),
                source_url=url,
                keywords=self._extract_keywords_sunat(name, description, url)
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo procedimiento SUNAT: {e}")
            return None

    async def _extract_gob_procedure(self, soup: BeautifulSoup, url: str) -> Optional[ProcedureData]:
        """Extractor especializado para gob.pe"""
        try:
            # Título específico de gob.pe
            name = self._extract_text_by_selectors(soup, ['h1', '.title', '.procedure-title'])
            
            # Descripción detallada
            description = self._extract_text_by_selectors(soup, 
                ['.description', '.procedure-description', '.content-description', '.summary'])
            
            # Entidad responsable
            entity_info = self._extract_entity_from_gob_pe(soup, url)
            
            # Información específica de gob.pe
            info_sections = soup.find_all(['div', 'section'], class_=re.compile(r'info|requirement|cost|time'))
            
            cost = 0.0
            processing_time = "No especificado"
            requirements = []
            
            # Extraer información estructurada de gob.pe
            for section in info_sections:
                section_text = section.get_text().lower()
                
                if 'costo' in section_text or 'precio' in section_text:
                    cost_match = re.search(r's/\.?\s*(\d+(?:\.\d{2})?)', section_text)
                    if cost_match:
                        cost = float(cost_match.group(1))
                
                if 'tiempo' in section_text or 'plazo' in section_text:
                    time_match = re.search(r'(\d+)\s*(día|días|hora|horas)', section_text)
                    if time_match:
                        processing_time = time_match.group(0)
                
                if 'requisito' in section_text:
                    req_list = section.find_all('li')
                    if req_list:
                        requirements.extend([li.get_text().strip() for li in req_list])
            
            # Si no encontró requisitos en secciones, buscar en listas generales
            if not requirements:
                requirements = self._extract_requirements_generic(soup)
            
            return ProcedureData(
                name=name or "Procedimiento gob.pe",
                description=description or "Procedimiento gubernamental",
                entity_name=entity_info['name'],
                entity_code=entity_info['code'],
                tupa_code=self._generate_code_from_url(url),
                requirements=requirements,
                cost=cost,
                currency="PEN",
                processing_time=processing_time,
                legal_basis=self._extract_legal_references(soup),
                channels=["Presencial", "Virtual"],
                category=self._categorize_generic_procedure(name, description),
                subcategory="",
                is_free=cost == 0,
                is_online=True,
                difficulty_level=self._assess_difficulty_generic(requirements, cost),
                source_url=url,
                keywords=self._extract_keywords_generic(name, description)
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo procedimiento gob.pe: {e}")
            return None

    async def _extract_reniec_procedure(self, soup: BeautifulSoup, url: str) -> Optional[ProcedureData]:
        """Extractor especializado para RENIEC"""
        try:
            name = self._extract_text_by_selectors(soup, ['h1', 'h2', '.titulo'])
            description = self._extract_text_by_selectors(soup, ['.descripcion', '.contenido'])
            
            # Información específica de RENIEC
            cost = 32.20  # Costo típico de trámites RENIEC
            processing_time = "48 horas"
            
            # Requisitos específicos de RENIEC
            requirements = self._extract_requirements_generic(soup)
            if not requirements:
                # Requisitos por defecto según tipo de trámite
                if 'duplicado' in name.lower():
                    requirements = [
                        "DNI deteriorado o denuncia policial",
                        "Recibo de pago por derecho de trámite",
                        "Foto actual tamaño carné",
                        "Presencia personal del solicitante"
                    ]
            
            return ProcedureData(
                name=name or "Trámite RENIEC",
                description=description or "Trámite de identificación",
                entity_name="RENIEC",
                entity_code="RENIEC",
                tupa_code=self._generate_code_from_url(url),
                requirements=requirements,
                cost=cost,
                currency="PEN",
                processing_time=processing_time,
                legal_basis=["Ley Nº 26497 - Ley Orgánica del RENIEC"],
                channels=["Presencial"],
                category="identidad",
                subcategory="dni",
                is_free=False,
                is_online=False,
                difficulty_level="easy",
                source_url=url,
                keywords=["dni", "reniec", "identificacion", "duplicado"]
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo procedimiento RENIEC: {e}")
            return None

    async def _extract_mtc_procedure(self, soup: BeautifulSoup, url: str) -> Optional[ProcedureData]:
        """Extractor especializado para MTC"""
        try:
            name = self._extract_text_by_selectors(soup, ['h1', '.title'])
            description = "TUPA Digital del Ministerio de Transportes y Comunicaciones"
            
            return ProcedureData(
                name=name or "TUPA Digital MTC",
                description=description,
                entity_name="MTC",
                entity_code="MTC",
                tupa_code="MTC-DIGITAL",
                requirements=["Consultar en plataforma digital"],
                cost=0.0,
                currency="PEN",
                processing_time="Consulta inmediata",
                legal_basis=["Ley Nº 27791 - Ley de Organización y Funciones del MTC"],
                channels=["Virtual"],
                category="vehicular",
                subcategory="tupa",
                is_free=True,
                is_online=True,
                difficulty_level="easy",
                source_url=url,
                keywords=["mtc", "transporte", "tupa", "digital"]
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo procedimiento MTC: {e}")
            return None

    async def _extract_generic_procedure(self, soup: BeautifulSoup, url: str) -> Optional[ProcedureData]:
        """Extractor genérico para otros sitios"""
        try:
            name = self._extract_text_by_selectors(soup, ['h1', 'h2', 'title'])
            description = self._extract_text_by_selectors(soup, ['p', '.description'])
            
            return ProcedureData(
                name=name or "Procedimiento Genérico",
                description=description or "Procedimiento gubernamental",
                entity_name="Gobierno del Perú",
                entity_code="GOB",
                tupa_code=self._generate_code_from_url(url),
                requirements=self._extract_requirements_generic(soup),
                cost=0.0,
                currency="PEN",
                processing_time="No especificado",
                legal_basis=[],
                channels=["Presencial"],
                category="general",
                subcategory="",
                is_free=True,
                is_online=False,
                difficulty_level="medium",
                source_url=url,
                keywords=self._extract_keywords_generic(name, description)
            )
            
        except Exception as e:
            logger.error(f"Error extrayendo procedimiento genérico: {e}")
            return None

    # Métodos auxiliares específicos

    def _extract_text_by_selectors(self, soup: BeautifulSoup, selectors: List[str], max_length: int = 200) -> str:
        """Extraer texto usando múltiples selectores"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 5:
                    return text[:max_length] if max_length else text
        return ""

    def _extract_requirements_sunat(self, soup: BeautifulSoup) -> List[str]:
        """Extraer requisitos específicos de SUNAT"""
        requirements = []
        
        # Buscar secciones específicas de SUNAT
        req_keywords = ['requisito', 'documento', 'presenta', 'adjunta']
        
        for keyword in req_keywords:
            sections = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for section in sections:
                parent = section.parent
                if parent:
                    # Buscar listas cerca de la sección
                    lists = parent.find_next_siblings(['ul', 'ol']) + parent.find_all(['ul', 'ol'])
                    for ul in lists:
                        items = ul.find_all('li')
                        for item in items:
                            req_text = item.get_text().strip()
                            if len(req_text) > 10 and len(req_text) < 200:
                                requirements.append(req_text)
        
        return list(set(requirements))[:8]  # Máximo 8, sin duplicados

    def _extract_requirements_generic(self, soup: BeautifulSoup) -> List[str]:
        """Extraer requisitos genéricos"""
        requirements = []
        
        # Buscar todas las listas
        lists = soup.find_all(['ul', 'ol'])
        for ul in lists:
            items = ul.find_all('li')
            for item in items:
                text = item.get_text().strip()
                if len(text) > 5 and len(text) < 200:
                    requirements.append(text)
        
        return requirements[:6]

    def _extract_legal_references(self, soup: BeautifulSoup) -> List[str]:
        """Extraer referencias legales"""
        text = soup.get_text()
        legal_patterns = [
            r'Ley\s+N?°?\s*\d+[^\n.]*',
            r'Decreto\s+\w+\s+N?°?\s*\d+[^\n.]*',
            r'Resolución\s+\w*\s*N?°?\s*\d+[^\n.]*'
        ]
        
        legal_refs = []
        for pattern in legal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            legal_refs.extend(matches[:2])  # Máximo 2 por patrón
        
        return legal_refs

    def _categorize_sunat_procedure(self, name: str, description: str, url: str) -> str:
        """Categorizar procedimiento de SUNAT"""
        text = f"{name} {description} {url}".lower()
        
        if any(word in text for word in ['importac', 'export', 'aduaner']):
            return 'aduanero'
        elif any(word in text for word in ['ruc', 'tributar', 'impuest']):
            return 'tributario'
        elif any(word in text for word in ['deposit', 'almacen']):
            return 'deposito'
        elif any(word in text for word in ['transit', 'transport']):
            return 'transito'
        else:
            return 'tributario'

    def _get_sunat_subcategory(self, url: str) -> str:
        """Obtener subcategoría de SUNAT basada en URL"""
        if 'importacion' in url:
            return 'importacion'
        elif 'exportacion' in url:
            return 'exportacion'
        elif 'perfeccionam' in url:
            return 'perfeccionamiento'
        elif 'deposito' in url:
            return 'deposito'
        elif 'transito' in url:
            return 'transito'
        elif 'especiales' in url:
            return 'especiales'
        else:
            return 'general'

    def _extract_entity_from_gob_pe(self, soup: BeautifulSoup, url: str) -> Dict[str, str]:
        """Extraer información de entidad desde gob.pe"""
        # Por defecto
        entity_name = "Gobierno del Perú"
        entity_code = "GOB"
        
        # Buscar indicadores de entidad específica
        text = soup.get_text().lower()
        
        if 'reniec' in text or 'dni' in url:
            entity_name = "RENIEC"
            entity_code = "RENIEC"
        elif 'sunat' in text:
            entity_name = "SUNAT"
            entity_code = "SUNAT"
        elif 'sunarp' in text:
            entity_name = "SUNARP"
            entity_code = "SUNARP"
        
        return {'name': entity_name, 'code': entity_code}

    def _categorize_generic_procedure(self, name: str, description: str) -> str:
        """Categorizar procedimiento genérico"""
        text = f"{name} {description}".lower()
        
        categories = {
            'identidad': ['dni', 'pasaporte', 'identificacion'],
            'empresarial': ['empresa', 'negocio', 'ruc'],
            'vehicular': ['licencia', 'conducir', 'vehiculo'],
            'salud': ['salud', 'medico', 'sanitario'],
            'educacion': ['educacion', 'titulo', 'certificado']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'

    def _assess_difficulty_sunat(self, requirements: List[str], cost: float) -> str:
        """Evaluar dificultad específica para SUNAT"""
        score = 0
        
        if len(requirements) > 6:
            score += 1
        if cost > 1000:
            score += 1
        
        # Palabras de complejidad específicas de SUNAT
        req_text = ' '.join(requirements).lower()
        complex_words = ['declaracion', 'aforo', 'valorizacion', 'arancel']
        if any(word in req_text for word in complex_words):
            score += 1
        
        return 'easy' if score <= 1 else 'medium' if score == 2 else 'hard'

    def _assess_difficulty_generic(self, requirements: List[str], cost: float) -> str:
        """Evaluar dificultad genérica"""
        score = 0
        
        if len(requirements) > 4:
            score += 1
        if cost > 50:
            score += 1
        
        return 'easy' if score <= 1 else 'medium'

    def _extract_keywords_sunat(self, name: str, description: str, url: str) -> List[str]:
        """Extraer keywords específicas de SUNAT"""
        base_keywords = ['sunat', 'aduanas', 'tributario']
        
        # Keywords de la URL
        if 'importacion' in url:
            base_keywords.extend(['importacion', 'mercancia'])
        if 'exportacion' in url:
            base_keywords.extend(['exportacion', 'comercio'])
        if 'transito' in url:
            base_keywords.extend(['transito', 'transporte'])
        
        return base_keywords

    def _extract_keywords_generic(self, name: str, description: str) -> List[str]:
        """Extraer keywords genéricas"""
        text = f"{name} {description}".lower()
        words = re.findall(r'\b\w{4,}\b', text)
        
        # Filtrar palabras comunes
        stop_words = {'gobierno', 'peru', 'procedimiento', 'tramite', 'solicitud'}
        keywords = [word for word in set(words) if word not in stop_words]
        
        return keywords[:6]

    def _generate_code_from_url(self, url: str) -> str:
        """Generar código TUPA desde URL"""
        path = urlparse(url).path
        
        # Para SUNAT
        if 'despa-pg' in path:
            code_match = re.search(r'despa-pg\.([^.]+)', path)
            if code_match:
                return f"SUNAT-PG-{code_match.group(1).upper()}"
        
        # Para otros
        path_parts = path.split('/')
        if len(path_parts) > 1:
            return f"GOB-{path_parts[-1].replace('.htm', '').replace('-', '').upper()[:10]}"
        
        return f"PROC-{hash(url) % 10000:04d}"

    async def save_results(self, procedures: List[ProcedureData], filename: str = 'specialized_procedures.json'):
        """Guardar resultados especializados"""
        results = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_procedures': len(procedures),
                'sources': list(set(proc.source_url for proc in procedures)),
                'entities': list(set(proc.entity_name for proc in procedures))
            },
            'procedures': [
                {
                    'name': proc.name,
                    'entity': proc.entity_name,
                    'code': proc.tupa_code,
                    'cost': proc.cost,
                    'processing_time': proc.processing_time,
                    'category': proc.category,
                    'subcategory': proc.subcategory,
                    'requirements_count': len(proc.requirements),
                    'is_free': proc.is_free,
                    'is_online': proc.is_online,
                    'difficulty': proc.difficulty_level,
                    'source_url': proc.source_url,
                    'full_data': {
                        'description': proc.description,
                        'requirements': proc.requirements,
                        'legal_basis': proc.legal_basis,
                        'channels': proc.channels,
                        'keywords': proc.keywords
                    }
                }
                for proc in procedures
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultados guardados en {filename}")

# Script principal para testing
async def main():
    """Función principal para testing"""
    scraper = SpecializedScraper()
    
    logger.info("Iniciando scraping especializado...")
    procedures = await scraper.scrape_specialized_urls()
    
    if procedures:
        logger.info(f"Extraídos {len(procedures)} procedimientos especializados")
        
        # Guardar resultados
        await scraper.save_results(procedures)
        
        # Mostrar resumen
        print("\n=== PROCEDIMIENTOS EXTRAÍDOS ===")
        for proc in procedures:
            print(f"- {proc.name} ({proc.entity_name}) - S/{proc.cost}")
    else:
        logger.warning("No se extrajeron procedimientos")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
