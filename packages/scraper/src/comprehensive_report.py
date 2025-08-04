#!/usr/bin/env python3
"""
Script para generar reporte comprensivo de toda la información extraída
"""

import json
import pandas as pd
from datetime import datetime
from pathlib import Path

def load_analysis_results():
    """Cargar resultados de todos los análisis"""
    
    results = {
        'pdf_analysis': None,
        'links_analysis': None,
        'excel_analysis': None,
        'pdf_file_exists': False,
        'links_file_exists': False,
        'excel_file_exists': False
    }
    
    # Cargar análisis de PDFs
    pdf_file = Path('pdf_analysis_simple.json')
    if pdf_file.exists():
        with open(pdf_file, 'r', encoding='utf-8') as f:
            results['pdf_analysis'] = json.load(f)
            results['pdf_file_exists'] = True
    
    # Cargar análisis de enlaces
    links_file = Path('links_analysis.json')
    if links_file.exists():
        with open(links_file, 'r', encoding='utf-8') as f:
            results['links_analysis'] = json.load(f)
            results['links_file_exists'] = True
    
    # Cargar análisis de Excel
    excel_file = Path('excel_analysis.json')
    if excel_file.exists():
        with open(excel_file, 'r', encoding='utf-8') as f:
            results['excel_analysis'] = json.load(f)
            results['excel_file_exists'] = True
    
    return results

def generate_comprehensive_report():
    """Generar reporte comprensivo de todas las fuentes"""
    
    print("📊 REPORTE COMPRENSIVO - TRAMITES AI")
    print("=" * 60)
    
    # Cargar datos
    data = load_analysis_results()
    
    if not data['pdf_file_exists'] and not data['links_file_exists'] and not data['excel_file_exists']:
        print("❌ No se encontraron archivos de análisis")
        return
    
    # Estadísticas generales
    print("📈 ESTADÍSTICAS GENERALES")
    print("-" * 40)
    
    total_procedures = 0
    sources_processed = 0
    
    # PDFs
    if data['pdf_file_exists']:
        pdf_data = data['pdf_analysis']
        pdf_procedures = pdf_data['summary']['total_procedures']
        pdf_count = pdf_data['summary']['total_pdfs']
        
        print(f"📄 PDFs analizados: {pdf_count}")
        print(f"📋 Procedimientos desde PDFs: {pdf_procedures}")
        
        total_procedures += pdf_procedures
        sources_processed += pdf_count
    
    # Enlaces
    if data['links_file_exists']:
        links_data = data['links_analysis']
        links_procedures = links_data['summary']['total_procedures']
        links_count = links_data['summary']['total_links']
        
        print(f"🔗 Enlaces analizados: {links_count}")
        print(f"📋 Procedimientos desde enlaces: {links_procedures}")
        
        total_procedures += links_procedures
        sources_processed += links_count
    
    # Excel
    if data['excel_file_exists']:
        excel_data = data['excel_analysis']
        excel_procedures = excel_data['summary']['total_procedures']
        excel_count = excel_data['summary']['total_files']
        excel_rows = excel_data['summary']['total_rows']
        
        print(f"📊 Archivos Excel analizados: {excel_count}")
        print(f"📊 Filas totales en Excel: {excel_rows}")
        print(f"📋 Procedimientos desde Excel: {excel_procedures}")
        
        total_procedures += excel_procedures
        sources_processed += excel_count
    
    print(f"\n🎯 TOTALES CONSOLIDADOS:")
    print(f"   • Fuentes procesadas: {sources_processed}")
    print(f"   • Procedimientos identificados: {total_procedures}")
    
    # Análisis por entidad
    print(f"\n🏛️ ANÁLISIS POR ENTIDAD")
    print("-" * 40)
    
    entity_stats = {}
    
    # Entidades desde PDFs
    if data['pdf_file_exists']:
        pdf_entities = data['pdf_analysis']['summary']['entities_found']
        for entity in pdf_entities:
            entity_stats[entity] = entity_stats.get(entity, {'pdfs': 0, 'links': 0, 'excel': 0, 'total': 0})
            entity_stats[entity]['pdfs'] = pdf_entities.count(entity)
            entity_stats[entity]['total'] += entity_stats[entity]['pdfs']
    
    # Entidades desde enlaces
    if data['links_file_exists']:
        links_entities = data['links_analysis']['summary']['by_entity']
        for entity, count in links_entities.items():
            entity_stats[entity] = entity_stats.get(entity, {'pdfs': 0, 'links': 0, 'excel': 0, 'total': 0})
            entity_stats[entity]['links'] = count
            entity_stats[entity]['total'] += count
    
    # Entidades desde Excel
    if data['excel_file_exists']:
        for file_data in data['excel_analysis']['files']:
            for entity in file_data.get('entities_mentioned', []):
                entity_stats[entity] = entity_stats.get(entity, {'pdfs': 0, 'links': 0, 'excel': 0, 'total': 0})
                entity_stats[entity]['excel'] += 1
                entity_stats[entity]['total'] += 1
    
    # Mostrar estadísticas por entidad
    for entity, stats in sorted(entity_stats.items(), key=lambda x: x[1]['total'], reverse=True):
        print(f"   • {entity}:")
        print(f"     - PDFs: {stats['pdfs']}")
        print(f"     - Enlaces: {stats['links']}")
        print(f"     - Excel: {stats['excel']}")
        print(f"     - Total: {stats['total']}")
    
    # Tipos de documentos
    if data['pdf_file_exists']:
        print(f"\n📑 TIPOS DE DOCUMENTOS (PDFs)")
        print("-" * 40)
        
        doc_types = data['pdf_analysis']['summary']['document_types']
        for doc_type, count in sorted(doc_types.items()):
            print(f"   • {doc_type}: {count} archivos")
    
    # Calidad de los datos
    print(f"\n✅ CALIDAD DE LOS DATOS")
    print("-" * 40)
    
    if data['links_file_exists']:
        links_summary = data['links_analysis']['summary']
        success_rate = (links_summary['successful'] / links_summary['total_links']) * 100
        print(f"   • Enlaces procesados exitosamente: {success_rate:.1f}%")
        print(f"   • Enlaces con errores: {links_summary['errors']}")
        print(f"   • Enlaces con timeout: {links_summary['timeouts']}")
    
    if data['pdf_file_exists']:
        pdf_summary = data['pdf_analysis']['summary']
        avg_procedures_per_pdf = pdf_summary['total_procedures'] / pdf_summary['total_pdfs']
        print(f"   • Promedio de procedimientos por PDF: {avg_procedures_per_pdf:.1f}")
    
    # Fuentes más productivas
    print(f"\n⭐ FUENTES MÁS PRODUCTIVAS")
    print("-" * 40)
    
    productive_sources = []
    
    # PDFs más productivos
    if data['pdf_file_exists']:
        for pdf_result in data['pdf_analysis']['detailed_results']:
            productive_sources.append({
                'type': 'PDF',
                'name': pdf_result['file_name'],
                'procedures': len(pdf_result['procedures_found']),
                'info': f"{pdf_result['document_type']} - {pdf_result['pages']} páginas"
            })
    
    # Enlaces más productivos
    if data['links_file_exists']:
        for link_result in data['links_analysis']['results']:
            if link_result['status'] == 'success':
                productive_sources.append({
                    'type': 'ENLACE',
                    'name': link_result['title'][:50] + "..." if len(link_result['title']) > 50 else link_result['title'],
                    'procedures': len(link_result['procedures_found']),
                    'info': f"{link_result['entity']} - {link_result['url'][:50]}..."
                })
    
    # Ordenar por productividad
    productive_sources.sort(key=lambda x: x['procedures'], reverse=True)
    
    for i, source in enumerate(productive_sources[:10], 1):
        print(f"   {i:2d}. {source['type']}: {source['name']}")
        print(f"       📋 {source['procedures']} procedimientos")
        print(f"       ℹ️  {source['info']}")
        print()
    
    # Generar archivo consolidado
    consolidated_data = {
        'generation_date': datetime.now().isoformat(),
        'summary': {
            'total_sources': sources_processed,
            'total_procedures': total_procedures,
            'sources_breakdown': {
                'pdfs': pdf_count if data['pdf_file_exists'] else 0,
                'links': links_count if data['links_file_exists'] else 0
            },
            'procedures_breakdown': {
                'from_pdfs': pdf_procedures if data['pdf_file_exists'] else 0,
                'from_links': links_procedures if data['links_file_exists'] else 0
            },
            'by_entity': entity_stats
        },
        'source_data': data
    }
    
    with open('comprehensive_report.json', 'w', encoding='utf-8') as f:
        json.dump(consolidated_data, f, ensure_ascii=False, indent=2)
    
    # Generar CSV para análisis
    print(f"📊 GENERANDO ARCHIVOS DE ANÁLISIS")
    print("-" * 40)
    
    # CSV de procedimientos consolidados
    procedures_data = []
    
    # Procedimientos desde PDFs
    if data['pdf_file_exists']:
        for pdf_result in data['pdf_analysis']['detailed_results']:
            for proc_text in pdf_result['procedures_found']:
                procedures_data.append({
                    'source_type': 'PDF',
                    'source_name': pdf_result['file_name'],
                    'entity': ', '.join(pdf_result['entities_mentioned']) if pdf_result['entities_mentioned'] else 'Unknown',
                    'document_type': pdf_result['document_type'],
                    'procedure_text': proc_text.strip()[:200],  # Limitar a 200 caracteres
                    'has_tables': pdf_result['has_tables'],
                    'pages': pdf_result['pages']
                })
    
    # Procedimientos desde enlaces
    if data['links_file_exists']:
        for link_result in data['links_analysis']['results']:
            if link_result['status'] == 'success':
                for proc_text in link_result['procedures_found']:
                    procedures_data.append({
                        'source_type': 'ENLACE',
                        'source_name': link_result['title'],
                        'entity': link_result['entity'],
                        'document_type': 'WEB',
                        'procedure_text': proc_text.strip()[:200],
                        'has_tables': False,
                        'pages': 1
                    })
    
    if procedures_data:
        df = pd.DataFrame(procedures_data)
        df.to_csv('consolidated_procedures.csv', index=False, encoding='utf-8')
        print(f"   ✅ consolidated_procedures.csv ({len(procedures_data)} registros)")
    
    # CSV de estadísticas por entidad
    entity_df_data = []
    for entity, stats in entity_stats.items():
        entity_df_data.append({
            'entity': entity,
            'sources_pdfs': stats['pdfs'],
            'sources_links': stats['links'],
            'total_sources': stats['total']
        })
    
    if entity_df_data:
        entity_df = pd.DataFrame(entity_df_data)
        entity_df.to_csv('entity_statistics.csv', index=False, encoding='utf-8')
        print(f"   ✅ entity_statistics.csv")
    
    print(f"   ✅ comprehensive_report.json")
    
    print(f"\n🎉 REPORTE COMPRENSIVO GENERADO EXITOSAMENTE")
    print(f"💡 Archivos generados listos para análisis posterior")

def main():
    """Función principal"""
    try:
        generate_comprehensive_report()
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")

if __name__ == "__main__":
    main()
