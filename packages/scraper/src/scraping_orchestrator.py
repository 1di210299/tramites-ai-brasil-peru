#!/usr/bin/env python3
"""
Orchestrador principal del sistema de scraping TUPA
Combina scraping y población de base de datos
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import argparse

# Importar módulos locales
from tupa_scraper import TupaScraper, ProcedureData
from database_integration import DatabaseIntegration
from specialized_scraper import SpecializedScraper
from pdf_processor import PDFProcessor

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ScrapingOrchestrator:
    """Orchestrador principal del sistema de scraping"""
    
    def __init__(self, database_url: str = None):
        self.scraper = TupaScraper()
        self.specialized_scraper = SpecializedScraper()
        self.pdf_processor = PDFProcessor()
        self.db = DatabaseIntegration(database_url)
        self.start_time = None
        
    async def run_full_process(self, save_to_db: bool = True, export_files: bool = True) -> Dict[str, Any]:
        """Ejecutar proceso completo de scraping y almacenamiento"""
        self.start_time = datetime.now()
        logger.info("=== INICIANDO PROCESO DE SCRAPING TUPA ===")
        
        results = {
            'start_time': self.start_time.isoformat(),
            'procedures_scraped': 0,
            'procedures_saved': 0,
            'errors': 0,
            'entities_processed': set(),
            'categories_found': set(),
            'duration_seconds': 0
        }
        
        try:
            # 1. Ejecutar scraping básico
            logger.info("Fase 1: Ejecutando scraping básico...")
            basic_procedures = await self.scraper.run_full_scraping()
            
            # 2. Ejecutar scraping especializado para URLs específicas
            logger.info("Fase 2: Ejecutando scraping especializado...")
            specialized_procedures = await self.specialized_scraper.scrape_specialized_urls()
            
            # 3. Procesar documentos PDF
            logger.info("Fase 3: Procesando documentos PDF...")
            pdf_procedures = await self.pdf_processor.process_all_documents()
            
            # 4. Combinar todos los procedimientos
            all_procedures = basic_procedures + specialized_procedures + pdf_procedures
            results['procedures_scraped'] = len(all_procedures)
            
            if not all_procedures:
                logger.warning("No se encontraron procedimientos")
                return results
            
            # 5. Recopilar estadísticas
            for proc in all_procedures:
                results['entities_processed'].add(proc.entity_name)
                results['categories_found'].add(proc.category)
            
            logger.info(f"Scraping total completado: {len(all_procedures)} procedimientos")
            logger.info(f"  - Básicos: {len(basic_procedures)}")
            logger.info(f"  - Especializados: {len(specialized_procedures)}")
            logger.info(f"  - De PDFs: {len(pdf_procedures)}")
            
            # 6. Guardar en base de datos
            if save_to_db:
                logger.info("Fase 4: Guardando en base de datos...")
                await self.db.setup_connection()
                
                save_stats = await self.db.save_procedures_batch(all_procedures)
                results['procedures_saved'] = save_stats['saved']
                results['errors'] += save_stats['errors']
                
                logger.info(f"Guardado en BD: {save_stats['saved']} procedimientos")
            
            # 7. Exportar archivos
            if export_files:
                logger.info("Fase 5: Exportando archivos...")
                await self._export_results(all_procedures)
            
            # 8. Generar reporte final
            await self._generate_final_report(all_procedures, results)
            
        except Exception as e:
            logger.error(f"Error en proceso principal: {e}")
            results['errors'] += 1
            raise
        
        finally:
            if self.db:
                await self.db.close_connection()
            
            # Calcular duración
            end_time = datetime.now()
            results['duration_seconds'] = (end_time - self.start_time).total_seconds()
            results['end_time'] = end_time.isoformat()
        
        return results
    
    async def _export_results(self, procedures: List[ProcedureData]):
        """Exportar resultados a archivos"""
        try:
            # JSON detallado
            self.scraper.save_to_json(procedures, 'tupa_procedures_complete.json')
            
            # CSV para análisis
            self.scraper.save_to_csv(procedures, 'tupa_procedures_analysis.csv')
            
            # JSON simplificado para frontend
            await self._export_frontend_json(procedures)
            
            logger.info("Archivos exportados exitosamente")
            
        except Exception as e:
            logger.error(f"Error exportando archivos: {e}")
    
    async def _export_frontend_json(self, procedures: List[ProcedureData]):
        """Exportar JSON optimizado para frontend"""
        import json
        
        frontend_data = {
            'metadata': {
                'total_procedures': len(procedures),
                'last_updated': datetime.now().isoformat(),
                'entities': list(set(p.entity_name for p in procedures)),
                'categories': list(set(p.category for p in procedures))
            },
            'procedures': []
        }
        
        for proc in procedures:
            frontend_data['procedures'].append({
                'id': proc.tupa_code or f"{proc.entity_code}-{hash(proc.name) % 1000}",
                'name': proc.name,
                'description': proc.description[:200] + '...' if len(proc.description) > 200 else proc.description,
                'entity': {
                    'name': proc.entity_name,
                    'code': proc.entity_code
                },
                'cost': proc.cost,
                'currency': proc.currency,
                'processing_time': proc.processing_time,
                'requirements_count': len(proc.requirements),
                'is_free': proc.is_free,
                'is_online': proc.is_online,
                'category': proc.category,
                'difficulty': proc.difficulty_level,
                'keywords': proc.keywords[:5]  # Solo primeras 5 keywords
            })
        
        with open('tupa_procedures_frontend.json', 'w', encoding='utf-8') as f:
            json.dump(frontend_data, f, ensure_ascii=False, indent=2)
        
        logger.info("JSON para frontend exportado")
    
    async def _generate_final_report(self, procedures: List[ProcedureData], results: Dict[str, Any]):
        """Generar reporte final detallado"""
        report = f"""
=== REPORTE DE SCRAPING TUPA ===
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duración: {results['duration_seconds']:.2f} segundos

ESTADÍSTICAS GENERALES:
- Procedimientos scrapeados: {results['procedures_scraped']}
- Procedimientos guardados en BD: {results['procedures_saved']}
- Errores encontrados: {results['errors']}

ENTIDADES PROCESADAS ({len(results['entities_processed'])}):
"""
        
        # Estadísticas por entidad
        entity_stats = {}
        for proc in procedures:
            entity_stats[proc.entity_name] = entity_stats.get(proc.entity_name, 0) + 1
        
        for entity, count in sorted(entity_stats.items()):
            report += f"- {entity}: {count} procedimientos\n"
        
        report += f"\nCATEGORÍAS ENCONTRADAS ({len(results['categories_found'])}):\n"
        
        # Estadísticas por categoría
        category_stats = {}
        for proc in procedures:
            category_stats[proc.category] = category_stats.get(proc.category, 0) + 1
        
        for category, count in sorted(category_stats.items()):
            report += f"- {category}: {count} procedimientos\n"
        
        # Estadísticas adicionales
        free_count = sum(1 for p in procedures if p.is_free)
        online_count = sum(1 for p in procedures if p.is_online)
        
        report += f"""
ESTADÍSTICAS ADICIONALES:
- Procedimientos gratuitos: {free_count} ({free_count/len(procedures)*100:.1f}%)
- Procedimientos online: {online_count} ({online_count/len(procedures)*100:.1f}%)

DISTRIBUCIÓN POR DIFICULTAD:
"""
        
        difficulty_stats = {}
        for proc in procedures:
            difficulty_stats[proc.difficulty_level] = difficulty_stats.get(proc.difficulty_level, 0) + 1
        
        for difficulty, count in sorted(difficulty_stats.items()):
            report += f"- {difficulty}: {count} procedimientos\n"
        
        # Top 10 procedimientos más costosos
        costly_procedures = sorted(procedures, key=lambda x: x.cost, reverse=True)[:10]
        report += f"\nTOP 10 PROCEDIMIENTOS MÁS COSTOSOS:\n"
        for i, proc in enumerate(costly_procedures, 1):
            report += f"{i}. {proc.name} - S/{proc.cost} ({proc.entity_name})\n"
        
        # Guardar reporte
        with open('scraping_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        # También mostrar en consola
        print(report)
        logger.info("Reporte final generado")
    
    async def run_incremental_update(self) -> Dict[str, Any]:
        """Ejecutar actualización incremental (solo nuevos procedimientos)"""
        logger.info("=== ACTUALIZACION INCREMENTAL ===")
        
        # TODO: Implementar lógica para detectar solo procedimientos nuevos
        # Por ahora, ejecutar proceso completo
        return await self.run_full_process()
    
    async def validate_database_integrity(self) -> Dict[str, Any]:
        """Validar integridad de datos en base de datos"""
        logger.info("=== VALIDACION DE INTEGRIDAD ===")
        
        await self.db.setup_connection()
        
        validation_results = {
            'total_procedures': 0,
            'entities_count': 0,
            'missing_data': [],
            'duplicate_codes': [],
            'invalid_costs': []
        }
        
        try:
            # Obtener estadísticas básicas
            stats = await self.db.get_procedures_count()
            validation_results.update(stats)
            
            # TODO: Implementar validaciones específicas
            # - Procedimientos sin requisitos
            # - Códigos TUPA duplicados
            # - Costos negativos o inválidos
            # - Entidades sin procedimientos
            
            logger.info("Validación completada")
            
        except Exception as e:
            logger.error(f"Error en validación: {e}")
        
        finally:
            await self.db.close_connection()
        
        return validation_results

async def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Sistema de Scraping TUPA')
    parser.add_argument('--mode', choices=['full', 'incremental', 'validate'], 
                       default='full', help='Modo de ejecución')
    parser.add_argument('--no-db', action='store_true', 
                       help='No guardar en base de datos')
    parser.add_argument('--no-export', action='store_true', 
                       help='No exportar archivos')
    parser.add_argument('--db-url', type=str, 
                       help='URL de base de datos personalizada')
    
    args = parser.parse_args()
    
    orchestrator = ScrapingOrchestrator(args.db_url)
    
    try:
        if args.mode == 'full':
            results = await orchestrator.run_full_process(
                save_to_db=not args.no_db,
                export_files=not args.no_export
            )
        elif args.mode == 'incremental':
            results = await orchestrator.run_incremental_update()
        elif args.mode == 'validate':
            results = await orchestrator.validate_database_integrity()
        
        print(f"\n=== PROCESO COMPLETADO ===")
        print(f"Duración: {results.get('duration_seconds', 0):.2f} segundos")
        print(f"Procedimientos procesados: {results.get('procedures_scraped', 0)}")
        print(f"Errores: {results.get('errors', 0)}")
        
    except KeyboardInterrupt:
        logger.info("Proceso interrumpido por usuario")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Configurar event loop para Windows si es necesario
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())
