#!/usr/bin/env python3
"""
Script simplificado para extraer información de los PDFs del usuario
"""

import os
import json
import PyPDF2
import pdfplumber
import re
from pathlib import Path
from datetime import datetime

def analyze_pdf_content(pdf_path):
    """Analizar contenido de un PDF específico"""
    
    content_info = {
        'file_name': pdf_path.name,
        'pages': 0,
        'text_content': '',
        'procedures_found': [],
        'entities_mentioned': [],
        'document_type': 'unknown',
        'has_tables': False,
        'cost_info': []
    }
    
    try:
        # Leer con PyPDF2 para información básica
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            content_info['pages'] = len(pdf_reader.pages)
            
            # Extraer texto de las primeras páginas
            text_parts = []
            for i in range(min(3, len(pdf_reader.pages))):
                page_text = pdf_reader.pages[i].extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            content_info['text_content'] = '\n'.join(text_parts)
    
    except Exception as e:
        print(f"   ⚠️ Error con PyPDF2: {e}")
    
    try:
        # Análisis detallado con pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages[:3]):  # Solo primeras 3 páginas
                
                # Buscar tablas
                tables = page.find_tables()
                if tables:
                    content_info['has_tables'] = True
                
                # Extraer texto de la página
                page_text = page.extract_text()
                if page_text:
                    content_info['text_content'] += '\n' + page_text
    
    except Exception as e:
        print(f"   ⚠️ Error con pdfplumber: {e}")
    
    # Análisis del contenido extraído
    text = content_info['text_content'].lower()
    
    # Detectar tipo de documento
    if 'tupa' in text:
        content_info['document_type'] = 'TUPA'
    elif 'tasas' in text or 'tarifa' in text:
        content_info['document_type'] = 'TASAS'
    elif 'manual' in text:
        content_info['document_type'] = 'MANUAL'
    elif 'reniec' in text:
        content_info['document_type'] = 'RENIEC'
    elif 'sunat' in text:
        content_info['document_type'] = 'SUNAT'
    elif 'mtc' in text:
        content_info['document_type'] = 'MTC'
    
    # Buscar entidades mencionadas
    entities = ['SUNAT', 'RENIEC', 'MTC', 'MIMP', 'MIDIS', 'MINEDU']
    for entity in entities:
        if entity.lower() in text:
            content_info['entities_mentioned'].append(entity)
    
    # Buscar información de procedimientos
    procedure_patterns = [
        r'procedimiento[^.]*',
        r'trámite[^.]*',
        r'servicio[^.]*',
        r'solicitud[^.]*'
    ]
    
    for pattern in procedure_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        content_info['procedures_found'].extend(matches[:5])  # Solo primeros 5
    
    # Buscar información de costos
    cost_patterns = [
        r's/?\s*\d+\.?\d*',
        r'soles?\s*\d+',
        r'nuevos soles?\s*\d+',
        r'gratuito',
        r'sin costo'
    ]
    
    for pattern in cost_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        content_info['cost_info'].extend(matches[:10])  # Solo primeros 10
    
    return content_info

def main():
    """Función principal"""
    
    print("🔍 ANÁLISIS SIMPLIFICADO DE PDFs")
    print("=" * 50)
    
    docs_path = Path("/Users/juandiegogutierrezcortez/tramites-ai-brasil-peru/docs")
    
    if not docs_path.exists():
        print(f"❌ Directorio no encontrado: {docs_path}")
        return
    
    # Buscar PDFs
    pdf_files = list(docs_path.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No se encontraron archivos PDF")
        return
    
    print(f"📄 Encontrados {len(pdf_files)} archivos PDF")
    print("-" * 30)
    
    results = []
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{i}. Procesando: {pdf_file.name}")
        
        try:
            size_mb = pdf_file.stat().st_size / (1024 * 1024)
            print(f"   📊 Tamaño: {size_mb:.2f} MB")
            
            # Analizar contenido
            content_info = analyze_pdf_content(pdf_file)
            
            print(f"   📖 Páginas: {content_info['pages']}")
            print(f"   📑 Tipo: {content_info['document_type']}")
            print(f"   🏛️ Entidades: {', '.join(content_info['entities_mentioned']) if content_info['entities_mentioned'] else 'No detectadas'}")
            print(f"   📋 Procedimientos encontrados: {len(content_info['procedures_found'])}")
            print(f"   💰 Info de costos: {len(content_info['cost_info'])}")
            print(f"   📊 Tablas: {'Sí' if content_info['has_tables'] else 'No'}")
            
            results.append(content_info)
            print("   ✅ Completado")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Generar resumen
    print(f"\n📊 RESUMEN GENERAL")
    print("-" * 30)
    
    total_pages = sum(r['pages'] for r in results)
    total_procedures = sum(len(r['procedures_found']) for r in results)
    
    # Contar tipos de documento
    doc_types = {}
    all_entities = set()
    
    for result in results:
        doc_type = result['document_type']
        doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
        all_entities.update(result['entities_mentioned'])
    
    print(f"📄 Total de PDFs procesados: {len(results)}")
    print(f"📖 Total de páginas: {total_pages}")
    print(f"📋 Total de procedimientos mencionados: {total_procedures}")
    print(f"🏛️ Entidades encontradas: {', '.join(sorted(all_entities))}")
    
    print(f"\n📑 Tipos de documento:")
    for doc_type, count in sorted(doc_types.items()):
        print(f"   • {doc_type}: {count} archivos")
    
    # PDFs más informativos
    print(f"\n⭐ PDFs más informativos:")
    sorted_results = sorted(results, key=lambda x: len(x['procedures_found']), reverse=True)
    
    for i, result in enumerate(sorted_results[:3], 1):
        print(f"   {i}. {result['file_name']}")
        print(f"      • {result['pages']} páginas")
        print(f"      • {len(result['procedures_found'])} procedimientos")
        print(f"      • Tipo: {result['document_type']}")
    
    # Guardar resultados
    final_results = {
        'analysis_date': datetime.now().isoformat(),
        'summary': {
            'total_pdfs': len(results),
            'total_pages': total_pages,
            'total_procedures': total_procedures,
            'document_types': doc_types,
            'entities_found': sorted(list(all_entities))
        },
        'detailed_results': results
    }
    
    with open('pdf_analysis_simple.json', 'w', encoding='utf-8') as f:
        json.dump(final_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Análisis guardado en: pdf_analysis_simple.json")
    
    # Mostrar algunos procedimientos encontrados
    print(f"\n📋 EJEMPLOS DE PROCEDIMIENTOS ENCONTRADOS:")
    print("-" * 45)
    
    all_procedures = []
    for result in results:
        all_procedures.extend(result['procedures_found'])
    
    unique_procedures = list(set(all_procedures))[:10]
    
    for i, proc in enumerate(unique_procedures, 1):
        clean_proc = proc.strip()[:80]
        print(f"   {i:2d}. {clean_proc}")
    
    print(f"\n🎉 Análisis completado exitosamente!")

if __name__ == "__main__":
    main()
