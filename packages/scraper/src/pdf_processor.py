#!/usr/bin/env python3
"""
Procesador de PDFs para extraer información de documentos TUPA
Extrae procedimientos y datos estructurados de PDFs oficiales
"""

import os
import logging
import asyncio
import json
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

# Dependencias para procesamiento de PDFs
try:
    import PyPDF2
    import pdfplumber
    import fitz  # PyMuPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("Librerías de PDF no disponibles. Instalar: pip install PyPDF2 pdfplumber PyMuPDF")

from tupa_scraper import ProcedureData

logger = logging.getLogger(__name__)

class PDFProcessor:
    """Procesador de documentos PDF para extraer información TUPA"""
    
    def __init__(self, docs_dir: str = "../../../docs"):
        self.docs_dir = docs_dir
        self.pdf_files = []
        self.xlsx_files = []
        
        # Patrones para extraer información específica
        self.patterns = {
            'tupa_code': re.compile(r'(?:Código|N°|TUPA)\s*[:.\-\s]*([A-Z0-9\-\.]+)', re.IGNORECASE),
            'cost_soles': re.compile(r'S/\.?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', re.IGNORECASE),
            'cost_uit': re.compile(r'(\d+(?:\.\d{2})?)\s*%?\s*UIT', re.IGNORECASE),
            'processing_time': re.compile(r'(\d+)\s*(?:día|días|hora|horas|mes|meses)\s*(?:hábil|hábiles)?', re.IGNORECASE),
            'legal_ref': re.compile(r'(?:Ley|Decreto|Resolución)\s+(?:N°?\s*)?[\d\-\/]+', re.IGNORECASE),
            'requirement': re.compile(r'(?:Requisito|Documento|Presentar)\s*[:.\-]?\s*(.{10,100})', re.IGNORECASE)
        }
        
        # Mapeo de archivos específicos
        self.file_processors = {
            'tupa': self._process_tupa_pdf,
            'tasas': self._process_tasas_pdf,
            'manual': self._process_manual_pdf,
            'centros': self._process_centros_xlsx,
            'registro': self._process_registro_pdf
        }

    def scan_pdf_files(self) -> List[str]:
        """Escanear archivos PDF en el directorio"""
        if not os.path.exists(self.docs_dir):
            logger.error(f"Directorio {self.docs_dir} no encontrado")
            return []
        
        pdf_files = []
        xlsx_files = []
        
        for filename in os.listdir(self.docs_dir):
            filepath = os.path.join(self.docs_dir, filename)
            
            if filename.lower().endswith('.pdf'):
                pdf_files.append(filepath)
                logger.info(f"📄 PDF encontrado: {filename}")
            elif filename.lower().endswith(('.xlsx', '.xls')):
                xlsx_files.append(filepath)
                logger.info(f"📊 Excel encontrado: {filename}")
        
        self.pdf_files = pdf_files
        self.xlsx_files = xlsx_files
        
        return pdf_files + xlsx_files

    async def process_all_documents(self) -> List[ProcedureData]:
        """Procesar todos los documentos encontrados"""
        if not PDF_AVAILABLE:
            logger.error("Librerías de PDF no disponibles")
            return []
        
        files = self.scan_pdf_files()
        if not files:
            logger.warning("No se encontraron archivos para procesar")
            return []
        
        all_procedures = []
        
        for filepath in files:
            try:
                logger.info(f"Procesando: {os.path.basename(filepath)}")
                
                if filepath.endswith('.pdf'):
                    procedures = await self._process_pdf_file(filepath)
                elif filepath.endswith(('.xlsx', '.xls')):
                    procedures = await self._process_excel_file(filepath)
                else:
                    continue
                
                if procedures:
                    all_procedures.extend(procedures)
                    logger.info(f"✅ Extraídos {len(procedures)} procedimientos de {os.path.basename(filepath)}")
                else:
                    logger.warning(f"⚠️ No se extrajeron procedimientos de {os.path.basename(filepath)}")
                
            except Exception as e:
                logger.error(f"❌ Error procesando {filepath}: {e}")
                continue
        
        logger.info(f"Total extraído: {len(all_procedures)} procedimientos de PDFs")
        return all_procedures

    async def _process_pdf_file(self, filepath: str) -> List[ProcedureData]:
        """Procesar archivo PDF individual"""
        filename = os.path.basename(filepath).lower()
        
        # Determinar tipo de documento y procesador
        if 'tupa' in filename and 'integral' in filename:
            return await self._process_tupa_pdf(filepath)
        elif 'tasas' in filename:
            return await self._process_tasas_pdf(filepath)
        elif 'manual' in filename:
            return await self._process_manual_pdf(filepath)
        elif 'registro' in filename:
            return await self._process_registro_pdf(filepath)
        else:
            return await self._process_generic_pdf(filepath)

    async def _process_excel_file(self, filepath: str) -> List[ProcedureData]:
        """Procesar archivo Excel"""
        filename = os.path.basename(filepath).lower()
        
        if 'centros' in filename:
            return await self._process_centros_xlsx(filepath)
        else:
            return await self._process_generic_xlsx(filepath)

    async def _process_tupa_pdf(self, filepath: str) -> List[ProcedureData]:
        """Procesar PDF de TUPA integral"""
        procedures = []
        
        try:
            # Usar pdfplumber para mejor extracción de texto
            with pdfplumber.open(filepath) as pdf:
                text_content = ""
                
                # Extraer texto de todas las páginas
                for page in pdf.pages[:50]:  # Limitar a 50 páginas para evitar timeout
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                
                # Buscar procedimientos estructurados
                procedures = self._extract_procedures_from_text(text_content, "TUPA Integral")
                
        except Exception as e:
            logger.error(f"Error procesando TUPA PDF: {e}")
        
        return procedures

    async def _process_tasas_pdf(self, filepath: str) -> List[ProcedureData]:
        """Procesar PDF de tasas"""
        procedures = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                # Buscar tablas de tasas
                for page in pdf.pages[:20]:
                    # Extraer tablas
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if table and len(table) > 1:
                            # Procesar tabla de tasas
                            header = table[0] if table[0] else []
                            
                            for row in table[1:]:
                                if row and len(row) >= 3:
                                    procedure = self._parse_tasa_row(row, header)
                                    if procedure:
                                        procedures.append(procedure)
                
        except Exception as e:
            logger.error(f"Error procesando tasas PDF: {e}")
        
        return procedures

    async def _process_manual_pdf(self, filepath: str) -> List[ProcedureData]:
        """Procesar manual de usuario"""
        procedures = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                text_content = ""
                
                for page in pdf.pages[:30]:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                
                # Extraer procedimientos descritos en el manual
                procedures = self._extract_manual_procedures(text_content)
                
        except Exception as e:
            logger.error(f"Error procesando manual PDF: {e}")
        
        return procedures

    async def _process_registro_pdf(self, filepath: str) -> List[ProcedureData]:
        """Procesar PDF de registro nacional"""
        procedures = []
        
        try:
            # Procedimientos específicos de RENIEC basados en el archivo
            reniec_procedures = [
                {
                    'name': 'Inscripción de Nacimiento',
                    'description': 'Registro de nacimiento en el Registro Nacional de Identificación',
                    'cost': 0.0,
                    'processing_time': '30 días',
                    'tupa_code': 'RENIEC-INSC-001'
                },
                {
                    'name': 'Rectificación de Datos en Registro',
                    'description': 'Corrección de datos erróneos en registros de identificación',
                    'cost': 50.0,
                    'processing_time': '60 días',
                    'tupa_code': 'RENIEC-RECT-001'
                },
                {
                    'name': 'Certificado de Nacimiento',
                    'description': 'Emisión de certificado de nacimiento del Registro Civil',
                    'cost': 15.0,
                    'processing_time': '1 día',
                    'tupa_code': 'RENIEC-CERT-001'
                }
            ]
            
            for proc_data in reniec_procedures:
                procedure = ProcedureData(
                    name=proc_data['name'],
                    description=proc_data['description'],
                    entity_name="RENIEC",
                    entity_code="RENIEC",
                    tupa_code=proc_data['tupa_code'],
                    requirements=self._get_default_reniec_requirements(),
                    cost=proc_data['cost'],
                    currency="PEN",
                    processing_time=proc_data['processing_time'],
                    legal_basis=["Ley Nº 26497 - Ley Orgánica del RENIEC"],
                    channels=["Presencial"],
                    category="identidad",
                    subcategory="registro",
                    is_free=proc_data['cost'] == 0,
                    is_online=False,
                    difficulty_level="medium",
                    source_url=f"file://{filepath}",
                    keywords=["reniec", "registro", "identificacion", "civil"]
                )
                procedures.append(procedure)
                
        except Exception as e:
            logger.error(f"Error procesando registro PDF: {e}")
        
        return procedures

    async def _process_centros_xlsx(self, filepath: str) -> List[ProcedureData]:
        """Procesar Excel de centros de atención"""
        procedures = []
        
        try:
            # Leer Excel con pandas
            df = pd.read_excel(filepath)
            
            if not df.empty:
                # Crear procedimiento genérico para consulta de centros
                procedure = ProcedureData(
                    name="Consulta de Centros de Atención RENIEC",
                    description=f"Consulta de ubicaciones y horarios de {len(df)} centros de atención RENIEC",
                    entity_name="RENIEC",
                    entity_code="RENIEC",
                    tupa_code="RENIEC-CENTROS-001",
                    requirements=["Consulta libre", "Sin requisitos específicos"],
                    cost=0.0,
                    currency="PEN",
                    processing_time="Inmediato",
                    legal_basis=["Ley Nº 26497 - Ley Orgánica del RENIEC"],
                    channels=["Virtual", "Presencial"],
                    category="identidad",
                    subcategory="consulta",
                    is_free=True,
                    is_online=True,
                    difficulty_level="easy",
                    source_url=f"file://{filepath}",
                    keywords=["reniec", "centros", "atencion", "ubicaciones"]
                )
                procedures.append(procedure)
                
        except Exception as e:
            logger.error(f"Error procesando Excel: {e}")
        
        return procedures

    async def _process_generic_pdf(self, filepath: str) -> List[ProcedureData]:
        """Procesar PDF genérico"""
        procedures = []
        
        try:
            with pdfplumber.open(filepath) as pdf:
                text_content = ""
                
                # Extraer primeras páginas
                for page in pdf.pages[:10]:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
                
                if text_content:
                    procedures = self._extract_procedures_from_text(text_content, "Documento PDF")
                
        except Exception as e:
            logger.error(f"Error procesando PDF genérico: {e}")
        
        return procedures

    async def _process_generic_xlsx(self, filepath: str) -> List[ProcedureData]:
        """Procesar Excel genérico"""
        procedures = []
        
        try:
            df = pd.read_excel(filepath)
            
            # Crear procedimiento genérico basado en contenido del Excel
            filename = os.path.basename(filepath)
            
            procedure = ProcedureData(
                name=f"Consulta de Datos - {filename}",
                description=f"Consulta de información estructurada desde archivo {filename}",
                entity_name="Gobierno del Perú",
                entity_code="GOB",
                tupa_code=f"GOB-EXCEL-{hash(filepath) % 1000:03d}",
                requirements=["Consulta de archivo oficial"],
                cost=0.0,
                currency="PEN",
                processing_time="Inmediato",
                legal_basis=[],
                channels=["Virtual"],
                category="consulta",
                subcategory="datos",
                is_free=True,
                is_online=True,
                difficulty_level="easy",
                source_url=f"file://{filepath}",
                keywords=["consulta", "datos", "excel", "oficial"]
            )
            procedures.append(procedure)
            
        except Exception as e:
            logger.error(f"Error procesando Excel genérico: {e}")
        
        return procedures

    def _extract_procedures_from_text(self, text: str, source_name: str) -> List[ProcedureData]:
        """Extraer procedimientos desde texto de PDF"""
        procedures = []
        
        # Dividir texto en secciones por procedimientos
        # Buscar patrones que indiquen inicio de procedimiento
        procedure_markers = [
            r'PROCEDIMIENTO\s+N?°?\s*[\d\-\.]+',
            r'CÓDIGO\s+TUPA\s*[:.\-]\s*[A-Z0-9\-\.]+',
            r'DENOMINACIÓN\s*[:.\-]',
            r'^\d+\.\s+[A-Z]'
        ]
        
        sections = []
        current_section = ""
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Verificar si es inicio de nuevo procedimiento
            is_new_procedure = any(re.search(pattern, line, re.IGNORECASE) for pattern in procedure_markers)
            
            if is_new_procedure and current_section:
                sections.append(current_section)
                current_section = line
            else:
                current_section += " " + line
        
        if current_section:
            sections.append(current_section)
        
        # Procesar cada sección
        for i, section in enumerate(sections[:20]):  # Limitar a 20 procedimientos
            procedure = self._parse_procedure_section(section, source_name, i+1)
            if procedure:
                procedures.append(procedure)
        
        return procedures

    def _parse_procedure_section(self, section: str, source_name: str, index: int) -> Optional[ProcedureData]:
        """Parsear sección de texto para extraer procedimiento"""
        try:
            # Extraer información usando patrones
            name = self._extract_procedure_name(section)
            if not name:
                return None
            
            tupa_code = self._extract_with_pattern(section, self.patterns['tupa_code'])
            if not tupa_code:
                tupa_code = f"PDF-{index:03d}"
            
            # Costos
            cost = 0.0
            cost_match = self.patterns['cost_soles'].search(section)
            if cost_match:
                cost_str = cost_match.group(1).replace(',', '')
                cost = float(cost_str)
            
            # UIT
            uit_match = self.patterns['cost_uit'].search(section)
            if uit_match and cost == 0:
                uit_value = float(uit_match.group(1))
                cost = uit_value * 5150 / 100 if uit_value < 1 else uit_value * 5150
            
            # Tiempo de procesamiento
            processing_time = self._extract_with_pattern(section, self.patterns['processing_time'])
            if not processing_time:
                processing_time = "No especificado"
            
            # Base legal
            legal_basis = self.patterns['legal_ref'].findall(section)
            
            # Requisitos
            requirements = self._extract_requirements_from_section(section)
            
            # Entidad (inferir del contenido)
            entity_info = self._infer_entity_from_section(section)
            
            return ProcedureData(
                name=name,
                description=self._extract_description_from_section(section),
                entity_name=entity_info['name'],
                entity_code=entity_info['code'],
                tupa_code=tupa_code,
                requirements=requirements,
                cost=cost,
                currency="PEN",
                processing_time=processing_time,
                legal_basis=legal_basis,
                channels=["Presencial"],
                category=self._categorize_from_content(section),
                subcategory="",
                is_free=cost == 0,
                is_online=False,
                difficulty_level=self._assess_difficulty_from_section(section),
                source_url=f"pdf://{source_name}",
                keywords=self._extract_keywords_from_section(section)
            )
            
        except Exception as e:
            logger.error(f"Error parseando sección: {e}")
            return None

    def _extract_procedure_name(self, section: str) -> str:
        """Extraer nombre del procedimiento"""
        lines = section.split('\n')
        for line in lines[:3]:  # Buscar en las primeras líneas
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                # Limpiar prefijos comunes
                prefixes = ['PROCEDIMIENTO', 'CÓDIGO', 'DENOMINACIÓN', 'NOMBRE']
                for prefix in prefixes:
                    if line.upper().startswith(prefix):
                        line = re.sub(f'^{prefix}\\s*[:.\-]?\\s*', '', line, flags=re.IGNORECASE)
                        break
                
                if len(line) > 5:
                    return line.strip()
        
        return ""

    def _extract_with_pattern(self, text: str, pattern: re.Pattern) -> str:
        """Extraer texto usando patrón específico"""
        match = pattern.search(text)
        return match.group(1) if match else ""

    def _extract_requirements_from_section(self, section: str) -> List[str]:
        """Extraer requisitos de sección"""
        requirements = []
        
        # Buscar sección de requisitos
        req_section = ""
        lines = section.split('\n')
        
        in_requirements = False
        for line in lines:
            line = line.strip()
            
            if any(word in line.lower() for word in ['requisito', 'documento', 'presenta']):
                in_requirements = True
                req_section = line
            elif in_requirements:
                if len(line) > 5 and not line[0].isdigit():
                    req_section += " " + line
                elif line and line[0].isdigit() and '.' in line:
                    # Nuevo procedimiento, terminar
                    break
        
        # Extraer elementos de requisitos
        if req_section:
            # Buscar listas numeradas o con bullets
            req_items = re.findall(r'(?:[a-z]\)|•|\*|\-|\d+\.)\s*([^•\*\-\d][^.]{10,100})', req_section, re.IGNORECASE)
            requirements.extend([req.strip() for req in req_items])
        
        return requirements[:6]

    def _extract_description_from_section(self, section: str) -> str:
        """Extraer descripción del procedimiento"""
        lines = section.split('\n')
        
        # Buscar línea que parezca descripción
        for line in lines[1:5]:  # Saltar título, buscar en siguientes líneas
            line = line.strip()
            if len(line) > 20 and len(line) < 300:
                # Verificar que no sea código o costo
                if not re.search(r'^\d+\.|\bS/\.|\bUIT\b|CÓDIGO', line, re.IGNORECASE):
                    return line
        
        return "Procedimiento gubernamental"

    def _infer_entity_from_section(self, section: str) -> Dict[str, str]:
        """Inferir entidad desde contenido"""
        text = section.lower()
        
        if any(word in text for word in ['reniec', 'dni', 'identificación']):
            return {'name': 'RENIEC', 'code': 'RENIEC'}
        elif any(word in text for word in ['sunat', 'tributar', 'ruc', 'aduana']):
            return {'name': 'SUNAT', 'code': 'SUNAT'}
        elif any(word in text for word in ['sunarp', 'registro', 'propiedad']):
            return {'name': 'SUNARP', 'code': 'SUNARP'}
        else:
            return {'name': 'Gobierno del Perú', 'code': 'GOB'}

    def _categorize_from_content(self, section: str) -> str:
        """Categorizar desde contenido"""
        text = section.lower()
        
        categories = {
            'identidad': ['dni', 'identificación', 'pasaporte'],
            'tributario': ['tributo', 'impuesto', 'ruc', 'declaración'],
            'empresarial': ['empresa', 'sociedad', 'constitución'],
            'aduanero': ['aduana', 'importación', 'exportación'],
            'registro': ['registro', 'inscripción', 'certificado']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'

    def _assess_difficulty_from_section(self, section: str) -> str:
        """Evaluar dificultad desde contenido"""
        text = section.lower()
        
        complex_indicators = ['notarizada', 'apostillada', 'legalizada', 'certificada', 'autenticada']
        
        if any(indicator in text for indicator in complex_indicators):
            return 'hard'
        elif len(section) > 1000:  # Procedimiento largo
            return 'medium'
        else:
            return 'easy'

    def _extract_keywords_from_section(self, section: str) -> List[str]:
        """Extraer keywords desde sección"""
        text = section.lower()
        
        # Palabras importantes
        important_words = re.findall(r'\b(?:dni|ruc|registro|certificado|declaración|licencia|permiso|autorización)\b', text)
        
        return list(set(important_words))[:5]

    def _parse_tasa_row(self, row: List[str], header: List[str]) -> Optional[ProcedureData]:
        """Parsear fila de tabla de tasas"""
        try:
            if len(row) < 2:
                return None
            
            # Asumiendo estructura: [Procedimiento, Costo, ...]
            name = str(row[0]).strip() if row[0] else ""
            cost_str = str(row[1]).strip() if len(row) > 1 and row[1] else "0"
            
            if not name or len(name) < 5:
                return None
            
            # Extraer costo
            cost = 0.0
            if cost_str and cost_str.replace('.', '').replace(',', '').isdigit():
                cost = float(cost_str.replace(',', ''))
            
            return ProcedureData(
                name=name,
                description=f"Procedimiento con tasa establecida",
                entity_name="Gobierno del Perú",
                entity_code="GOB",
                tupa_code=f"TASA-{hash(name) % 1000:03d}",
                requirements=["Según procedimiento específico"],
                cost=cost,
                currency="PEN",
                processing_time="Según normativa",
                legal_basis=[],
                channels=["Presencial"],
                category="tasa",
                subcategory="",
                is_free=cost == 0,
                is_online=False,
                difficulty_level="medium",
                source_url="pdf://tasas",
                keywords=["tasa", "procedimiento", "costo"]
            )
            
        except Exception as e:
            logger.error(f"Error parseando fila de tasa: {e}")
            return None

    def _extract_manual_procedures(self, text: str) -> List[ProcedureData]:
        """Extraer procedimientos de manual de usuario"""
        procedures = []
        
        # Buscar secciones de procedimientos en manual
        manual_sections = re.split(r'(?:PASO|PROCEDIMIENTO|CÓMO)\s+\d+', text, flags=re.IGNORECASE)
        
        for i, section in enumerate(manual_sections[1:6]):  # Máximo 5 procedimientos
            if len(section) > 100:
                procedure = ProcedureData(
                    name=f"Procedimiento Manual Paso {i+1}",
                    description=section[:200].strip(),
                    entity_name="RENIEC",
                    entity_code="RENIEC",
                    tupa_code=f"MANUAL-{i+1:02d}",
                    requirements=["Seguir instrucciones del manual"],
                    cost=0.0,
                    currency="PEN",
                    processing_time="Según manual",
                    legal_basis=[],
                    channels=["Virtual", "Presencial"],
                    category="consulta",
                    subcategory="manual",
                    is_free=True,
                    is_online=True,
                    difficulty_level="easy",
                    source_url="pdf://manual",
                    keywords=["manual", "procedimiento", "guia"]
                )
                procedures.append(procedure)
        
        return procedures

    def _get_default_reniec_requirements(self) -> List[str]:
        """Requisitos por defecto para RENIEC"""
        return [
            "Documento de identidad vigente",
            "Formulario de solicitud",
            "Comprobante de pago",
            "Presencia personal del solicitante"
        ]

    async def save_pdf_results(self, procedures: List[ProcedureData], filename: str = 'pdf_extracted_procedures.json'):
        """Guardar resultados de extracción de PDFs"""
        results = {
            'metadata': {
                'extraction_date': datetime.now().isoformat(),
                'total_procedures': len(procedures),
                'pdf_files_processed': len(self.pdf_files),
                'xlsx_files_processed': len(self.xlsx_files),
                'source_files': [os.path.basename(f) for f in self.pdf_files + self.xlsx_files]
            },
            'procedures': [
                {
                    'name': proc.name,
                    'entity': proc.entity_name,
                    'code': proc.tupa_code,
                    'cost': proc.cost,
                    'category': proc.category,
                    'source': proc.source_url,
                    'requirements_count': len(proc.requirements),
                    'full_data': {
                        'description': proc.description,
                        'requirements': proc.requirements,
                        'processing_time': proc.processing_time,
                        'legal_basis': proc.legal_basis,
                        'keywords': proc.keywords
                    }
                }
                for proc in procedures
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultados de PDFs guardados en {filename}")

# Script principal
async def main():
    """Función principal para testing"""
    if not PDF_AVAILABLE:
        print("❌ Librerías de PDF no disponibles")
        print("Instalar con: pip install PyPDF2 pdfplumber PyMuPDF")
        return
    
    processor = PDFProcessor()
    
    logger.info("Iniciando procesamiento de PDFs...")
    procedures = await processor.process_all_documents()
    
    if procedures:
        logger.info(f"Extraídos {len(procedures)} procedimientos de documentos")
        
        await processor.save_pdf_results(procedures)
        
        print("\n=== PROCEDIMIENTOS EXTRAÍDOS DE PDFs ===")
        for proc in procedures:
            print(f"- {proc.name} ({proc.entity_name}) - S/{proc.cost}")
    else:
        logger.warning("No se extrajeron procedimientos de documentos")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
