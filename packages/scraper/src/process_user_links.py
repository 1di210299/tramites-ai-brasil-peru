#!/usr/bin/env python3
"""
Script para procesar específicamente los enlaces proporcionados por el usuario
Ejecuta scraping dirigido a los URLs más importantes
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Agregar src al path
sys.path.append(os.path.dirname(__file__))

from specialized_scraper import SpecializedScraper
from pdf_processor import PDFProcessor
from database_integration import DatabaseIntegration

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def process_user_links():
    """Procesar específicamente los enlaces del usuario"""
    print("🚀 Procesando enlaces específicos del usuario...")
    print("=" * 60)
    
    # 1. Procesar URLs especializados
    print("\n📋 FASE 1: Procesando URLs especializados")
    print("-" * 40)
    
    specialized_scraper = SpecializedScraper()
    url_procedures = await specialized_scraper.scrape_specialized_urls()
    
    print(f"✅ URLs procesados: {len(url_procedures)} procedimientos extraídos")
    
    # Mostrar muestra de URLs procesados
    for i, proc in enumerate(url_procedures[:5]):
        print(f"   {i+1}. {proc.name} ({proc.entity_name}) - S/{proc.cost}")
    
    if len(url_procedures) > 5:
        print(f"   ... y {len(url_procedures) - 5} más")
    
    # 2. Procesar documentos PDF
    print("\n📄 FASE 2: Procesando documentos PDF")
    print("-" * 40)
    
    pdf_processor = PDFProcessor()
    pdf_procedures = await pdf_processor.process_all_documents()
    
    print(f"✅ PDFs procesados: {len(pdf_procedures)} procedimientos extraídos")
    
    # Mostrar muestra de PDFs procesados
    for i, proc in enumerate(pdf_procedures[:5]):
        print(f"   {i+1}. {proc.name} ({proc.entity_name}) - S/{proc.cost}")
    
    if len(pdf_procedures) > 5:
        print(f"   ... y {len(pdf_procedures) - 5} más")
    
    # 3. Combinar resultados
    all_procedures = url_procedures + pdf_procedures
    
    print("\n📊 FASE 3: Resumen de datos extraídos")
    print("-" * 40)
    
    # Estadísticas por entidad
    entity_stats = {}
    category_stats = {}
    cost_stats = {'free': 0, 'paid': 0, 'total_cost': 0}
    
    for proc in all_procedures:
        # Por entidad
        entity_stats[proc.entity_name] = entity_stats.get(proc.entity_name, 0) + 1
        
        # Por categoría
        category_stats[proc.category] = category_stats.get(proc.category, 0) + 1
        
        # Por costo
        if proc.is_free:
            cost_stats['free'] += 1
        else:
            cost_stats['paid'] += 1
            cost_stats['total_cost'] += proc.cost
    
    print(f"📈 Total de procedimientos: {len(all_procedures)}")
    print(f"   • Desde URLs: {len(url_procedures)}")
    print(f"   • Desde PDFs: {len(pdf_procedures)}")
    
    print(f"\n🏛️ Por entidad:")
    for entity, count in sorted(entity_stats.items()):
        print(f"   • {entity}: {count} procedimientos")
    
    print(f"\n📑 Por categoría:")
    for category, count in sorted(category_stats.items()):
        print(f"   • {category}: {count} procedimientos")
    
    print(f"\n💰 Por costo:")
    print(f"   • Gratuitos: {cost_stats['free']}")
    print(f"   • Con costo: {cost_stats['paid']}")
    if cost_stats['paid'] > 0:
        avg_cost = cost_stats['total_cost'] / cost_stats['paid']
        print(f"   • Costo promedio: S/{avg_cost:.2f}")
    
    # 4. Guardar resultados especializados
    print("\n💾 FASE 4: Guardando resultados")
    print("-" * 40)
    
    # Guardar JSON especializado
    await specialized_scraper.save_results(url_procedures, 'urls_especializados.json')
    await pdf_processor.save_pdf_results(pdf_procedures, 'pdfs_procesados.json')
    
    # Guardar resumen combinado
    combined_results = {
        'metadata': {
            'extraction_date': datetime.now().isoformat(),
            'total_procedures': len(all_procedures),
            'url_procedures': len(url_procedures),
            'pdf_procedures': len(pdf_procedures),
            'entities': list(entity_stats.keys()),
            'categories': list(category_stats.keys())
        },
        'statistics': {
            'by_entity': entity_stats,
            'by_category': category_stats,
            'by_cost': cost_stats
        },
        'procedures': [
            {
                'name': proc.name,
                'entity': proc.entity_name,
                'code': proc.tupa_code,
                'cost': proc.cost,
                'currency': proc.currency,
                'processing_time': proc.processing_time,
                'category': proc.category,
                'is_free': proc.is_free,
                'is_online': proc.is_online,
                'difficulty': proc.difficulty_level,
                'source': proc.source_url,
                'requirements_count': len(proc.requirements)
            }
            for proc in all_procedures
        ]
    }
    
    import json
    with open('resultados_especializados.json', 'w', encoding='utf-8') as f:
        json.dump(combined_results, f, ensure_ascii=False, indent=2)
    
    print("✅ Archivos guardados:")
    print("   • urls_especializados.json")
    print("   • pdfs_procesados.json")
    print("   • resultados_especializados.json")
    
    # 5. Guardar en base de datos (opcional)
    print("\n🗄️ FASE 5: Integrando con base de datos")
    print("-" * 40)
    
    try:
        db = DatabaseIntegration()
        await db.setup_connection()
        
        save_stats = await db.save_procedures_batch(all_procedures)
        
        print(f"✅ Base de datos actualizada:")
        print(f"   • Guardados: {save_stats['saved']}")
        print(f"   • Omitidos: {save_stats['skipped']}")
        print(f"   • Errores: {save_stats['errors']}")
        
        await db.close_connection()
        
    except Exception as e:
        print(f"⚠️ No se pudo conectar a la base de datos: {e}")
        print("   (Los datos se guardaron en archivos JSON)")
    
    # 6. Mostrar procedimientos más relevantes
    print("\n⭐ PROCEDIMIENTOS MÁS RELEVANTES")
    print("-" * 40)
    
    # Filtrar procedimientos importantes
    important_procedures = [
        proc for proc in all_procedures 
        if any(keyword in proc.name.lower() for keyword in ['dni', 'ruc', 'licencia', 'registro', 'certificado'])
    ]
    
    for i, proc in enumerate(important_procedures[:10]):
        status = "🆓" if proc.is_free else f"💰 S/{proc.cost}"
        online = "🌐" if proc.is_online else "🏢"
        print(f"   {i+1:2d}. {proc.name[:50]:<50} {status} {online}")
        print(f"       {proc.entity_name} | {proc.category} | {proc.processing_time}")
        print()
    
    print("\n🎉 ¡Procesamiento completado exitosamente!")
    print(f"Total: {len(all_procedures)} procedimientos extraídos de tus fuentes específicas")
    
    return all_procedures

async def main():
    """Función principal"""
    try:
        start_time = datetime.now()
        
        procedures = await process_user_links()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n⏱️ Tiempo total: {duration:.2f} segundos")
        print(f"📊 Rendimiento: {len(procedures)/duration:.2f} procedimientos/segundo")
        
    except KeyboardInterrupt:
        print("\n⚠️ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")
        logger.error(f"Error fatal: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
