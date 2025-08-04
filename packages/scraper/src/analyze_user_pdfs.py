#!/usr/bin/env python3
"""
Analizador específico para los PDFs proporcionados por el usuario
"""

import os
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
import asyncio

# Importar procesadores
import sys
sys.path.append(os.path.dirname(__file__))

from pdf_processor import PDFProcessor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UserPDFAnalyzer:
    """Analizador específico para PDFs del usuario"""
    
    def __init__(self, docs_path="/Users/juandiegogutierrezcortez/tramites-ai-brasil-peru/docs"):
        self.docs_path = Path(docs_path)
        self.pdf_processor = PDFProcessor()
        
    async def analyze_user_pdfs(self):
        """Analizar todos los PDFs proporcionados por el usuario"""
        
        print("🔍 Analizando PDFs proporcionados...")
        print("=" * 50)
        
        if not self.docs_path.exists():
            print(f"❌ Directorio no encontrado: {self.docs_path}")
            return []
        
        # Buscar todos los PDFs
        pdf_files = list(self.docs_path.glob("*.pdf"))
        
        if not pdf_files:
            print(f"⚠️ No se encontraron PDFs en: {self.docs_path}")
            return []
        
        print(f"📄 Encontrados {len(pdf_files)} archivos PDF:")
        for i, pdf_file in enumerate(pdf_files, 1):
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            print(f"   {i}. {pdf_file.name} ({size_mb:.2f} MB)")
        
        print("\n🔄 Procesando cada PDF...")
        print("-" * 40)
        
        all_results = []
        
        for pdf_file in pdf_files:
            print(f"\n📖 Procesando: {pdf_file.name}")
            
            try:
                # Análisis básico del PDF
                basic_info = await self._analyze_pdf_structure(pdf_file)
                print(f"   • Páginas: {basic_info['pages']}")
                print(f"   • Tipo detectado: {basic_info['document_type']}")
                
                # Extracción de procedimientos
                procedures = await self.pdf_processor.process_single_pdf(str(pdf_file))
                print(f"   • Procedimientos extraídos: {len(procedures)}")
                
                # Estadísticas del PDF
                if procedures:
                    entities = set(proc.entity_name for proc in procedures)
                    categories = set(proc.category for proc in procedures)
                    free_count = sum(1 for proc in procedures if proc.is_free)
                    
                    print(f"   • Entidades: {', '.join(entities)}")
                    print(f"   • Categorías: {len(categories)}")
                    print(f"   • Gratuitos: {free_count}/{len(procedures)}")
                
                # Agregar a resultados
                pdf_result = {
                    'file': pdf_file.name,
                    'path': str(pdf_file),
                    'basic_info': basic_info,
                    'procedures': procedures,
                    'stats': {
                        'total_procedures': len(procedures),
                        'entities': list(entities) if procedures else [],
                        'categories': list(categories) if procedures else [],
                        'free_procedures': free_count if procedures else 0
                    }
                }
                
                all_results.append(pdf_result)
                
                print(f"   ✅ Completado")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                logger.error(f"Error procesando {pdf_file.name}: {e}")
        
        return all_results
    
    async def _analyze_pdf_structure(self, pdf_path):
        """Analizar la estructura básica del PDF"""
        
        try:
            import PyPDF2
            import pdfplumber
            
            basic_info = {
                'pages': 0,
                'has_tables': False,
                'has_forms': False,
                'document_type': 'unknown',
                'text_density': 'low'
            }
            
            # Análisis con PyPDF2
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                basic_info['pages'] = len(pdf_reader.pages)
                
                # Detectar formularios
                if pdf_reader.pages[0].get('/Annots'):
                    basic_info['has_forms'] = True
            
            # Análisis con pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                
                # Detectar tablas
                tables = first_page.find_tables()
                if tables:
                    basic_info['has_tables'] = True
                
                # Analizar contenido de texto
                text = first_page.extract_text() or ""
                
                # Detectar tipo de documento
                text_lower = text.lower()
                if 'tupa' in text_lower:
                    basic_info['document_type'] = 'TUPA'
                elif 'tasas' in text_lower or 'tarifa' in text_lower:
                    basic_info['document_type'] = 'TASAS'
                elif 'manual' in text_lower or 'procedimiento' in text_lower:
                    basic_info['document_type'] = 'MANUAL'
                elif 'formulario' in text_lower:
                    basic_info['document_type'] = 'FORMULARIO'
                elif 'decreto' in text_lower or 'ley' in text_lower:
                    basic_info['document_type'] = 'NORMATIVO'
                
                # Densidad de texto
                if len(text) > 2000:
                    basic_info['text_density'] = 'high'
                elif len(text) > 500:
                    basic_info['text_density'] = 'medium'
            
            return basic_info
            
        except Exception as e:
            logger.error(f"Error analizando estructura de {pdf_path}: {e}")
            return basic_info
    
    async def generate_comprehensive_report(self, results):
        """Generar reporte comprensivo de todos los PDFs"""
        
        print("\n📊 REPORTE COMPRENSIVO DE PDFs")
        print("=" * 50)
        
        # Estadísticas generales
        total_pdfs = len(results)
        total_procedures = sum(r['stats']['total_procedures'] for r in results)
        total_pages = sum(r['basic_info']['pages'] for r in results)
        
        print(f"📄 Total de PDFs analizados: {total_pdfs}")
        print(f"📋 Total de procedimientos extraídos: {total_procedures}")
        print(f"📖 Total de páginas procesadas: {total_pages}")
        
        # Por tipo de documento
        doc_types = {}
        for result in results:
            doc_type = result['basic_info']['document_type']
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        
        print(f"\n📑 Tipos de documento:")
        for doc_type, count in sorted(doc_types.items()):
            print(f"   • {doc_type}: {count} archivos")
        
        # Entidades más frecuentes
        all_entities = []
        for result in results:
            all_entities.extend(result['stats']['entities'])
        
        entity_count = {}
        for entity in all_entities:
            entity_count[entity] = entity_count.get(entity, 0) + 1
        
        print(f"\n🏛️ Entidades más frecuentes:")
        for entity, count in sorted(entity_count.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   • {entity}: {count} procedimientos")
        
        # PDFs más productivos
        print(f"\n⭐ PDFs más productivos:")
        sorted_results = sorted(results, key=lambda x: x['stats']['total_procedures'], reverse=True)
        
        for i, result in enumerate(sorted_results[:5], 1):
            stats = result['stats']
            print(f"   {i}. {result['file']}")
            print(f"      • {stats['total_procedures']} procedimientos")
            print(f"      • {len(stats['entities'])} entidades")
            print(f"      • {stats['free_procedures']} gratuitos")
        
        # Guardar reporte detallado
        report_data = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'total_pdfs': total_pdfs,
                'total_procedures': total_procedures,
                'total_pages': total_pages
            },
            'summary': {
                'document_types': doc_types,
                'entity_distribution': entity_count,
                'average_procedures_per_pdf': total_procedures / total_pdfs if total_pdfs > 0 else 0
            },
            'detailed_results': results
        }
        
        # Guardar JSON
        with open('pdf_analysis_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)
        
        # Generar CSV para análisis
        procedures_data = []
        for result in results:
            for proc in result['procedures']:
                procedures_data.append({
                    'source_pdf': result['file'],
                    'procedure_name': proc.name,
                    'entity': proc.entity_name,
                    'category': proc.category,
                    'cost': proc.cost,
                    'is_free': proc.is_free,
                    'processing_time': proc.processing_time,
                    'requirements_count': len(proc.requirements),
                    'is_online': proc.is_online,
                    'difficulty': proc.difficulty_level
                })
        
        if procedures_data:
            df = pd.DataFrame(procedures_data)
            df.to_csv('pdf_procedures_analysis.csv', index=False, encoding='utf-8')
            print(f"\n✅ Archivos generados:")
            print(f"   • pdf_analysis_report.json")
            print(f"   • pdf_procedures_analysis.csv")
        
        return report_data

async def main():
    """Función principal"""
    print("🚀 Iniciando análisis de PDFs del usuario")
    print("=" * 60)
    
    analyzer = UserPDFAnalyzer()
    
    try:
        # Analizar PDFs
        results = await analyzer.analyze_user_pdfs()
        
        if results:
            # Generar reporte
            await analyzer.generate_comprehensive_report(results)
            print(f"\n🎉 Análisis completado exitosamente!")
        else:
            print(f"\n⚠️ No se pudieron procesar PDFs")
    
    except Exception as e:
        print(f"\n❌ Error durante el análisis: {e}")
        logger.error(f"Error fatal: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
