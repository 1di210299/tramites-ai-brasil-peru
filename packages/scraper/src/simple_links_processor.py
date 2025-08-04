#!/usr/bin/env python3
"""
Script simplificado para procesar los enlaces del archivo links.txt
"""

import requests
import json
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

def extract_content_from_url(url):
    """Extraer contenido básico de una URL"""
    
    result = {
        'url': url,
        'title': '',
        'content_preview': '',
        'procedures_found': [],
        'entity': 'unknown',
        'status': 'success',
        'error': None
    }
    
    try:
        print(f"   📡 Conectando a: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parsear HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraer título
        title_tag = soup.find('title')
        if title_tag:
            result['title'] = title_tag.get_text().strip()
        
        # Extraer texto del cuerpo
        body_text = ""
        if soup.body:
            # Remover scripts y estilos
            for script in soup(["script", "style"]):
                script.decompose()
            body_text = soup.body.get_text()
        
        # Limpiar texto
        lines = (line.strip() for line in body_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        body_text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Guardar preview del contenido
        result['content_preview'] = body_text[:500] + "..." if len(body_text) > 500 else body_text
        
        # Detectar entidad basada en URL
        url_lower = url.lower()
        if 'sunat' in url_lower:
            result['entity'] = 'SUNAT'
        elif 'reniec' in url_lower:
            result['entity'] = 'RENIEC'
        elif 'mtc' in url_lower:
            result['entity'] = 'MTC'
        elif 'gob.pe' in url_lower:
            result['entity'] = 'GOB.PE'
        
        # Buscar palabras clave de procedimientos
        text_lower = body_text.lower()
        procedure_keywords = [
            'procedimiento', 'trámite', 'solicitud', 'registro', 
            'certificado', 'licencia', 'permiso', 'autorización',
            'inscripción', 'renovación', 'duplicado', 'canje'
        ]
        
        for keyword in procedure_keywords:
            if keyword in text_lower:
                # Buscar contexto alrededor de la palabra clave
                pattern = rf'.{{0,50}}{keyword}.{{0,50}}'
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                result['procedures_found'].extend(matches[:3])  # Solo primeros 3
        
        print(f"   ✅ Procesado: {result['title'][:60]}...")
        print(f"   📋 Procedimientos encontrados: {len(result['procedures_found'])}")
        
    except requests.exceptions.Timeout:
        result['status'] = 'timeout'
        result['error'] = 'Timeout al conectar'
        print(f"   ⏰ Timeout: {url}")
        
    except requests.exceptions.RequestException as e:
        result['status'] = 'error'
        result['error'] = str(e)
        print(f"   ❌ Error: {str(e)}")
        
    except Exception as e:
        result['status'] = 'error'
        result['error'] = f"Error inesperado: {str(e)}"
        print(f"   ⚠️ Error inesperado: {str(e)}")
    
    return result

def process_links_file():
    """Procesar el archivo links.txt"""
    
    print("🔗 PROCESANDO ENLACES ESPECÍFICOS")
    print("=" * 50)
    
    links_file = Path("/Users/juandiegogutierrezcortez/tramites-ai-brasil-peru/docs/links.txt")
    
    if not links_file.exists():
        print(f"❌ Archivo no encontrado: {links_file}")
        return []
    
    # Leer enlaces
    with open(links_file, 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
    
    print(f"📋 Encontrados {len(links)} enlaces")
    print("-" * 30)
    
    results = []
    
    for i, url in enumerate(links, 1):
        print(f"\n{i:2d}/{len(links)}. Procesando:")
        print(f"     {url}")
        
        result = extract_content_from_url(url)
        results.append(result)
    
    return results

def generate_links_report(results):
    """Generar reporte de enlaces procesados"""
    
    print("\n📊 REPORTE DE ENLACES")
    print("=" * 40)
    
    # Estadísticas generales
    total_links = len(results)
    successful = len([r for r in results if r['status'] == 'success'])
    errors = len([r for r in results if r['status'] == 'error'])
    timeouts = len([r for r in results if r['status'] == 'timeout'])
    
    print(f"📋 Total de enlaces: {total_links}")
    print(f"✅ Exitosos: {successful}")
    print(f"❌ Errores: {errors}")
    print(f"⏰ Timeouts: {timeouts}")
    
    # Por entidad
    entity_stats = {}
    total_procedures = 0
    
    for result in results:
        if result['status'] == 'success':
            entity = result['entity']
            entity_stats[entity] = entity_stats.get(entity, 0) + 1
            total_procedures += len(result['procedures_found'])
    
    print(f"\n🏛️ Por entidad:")
    for entity, count in sorted(entity_stats.items()):
        print(f"   • {entity}: {count} enlaces")
    
    print(f"\n📋 Total de procedimientos encontrados: {total_procedures}")
    
    # Enlaces más informativos
    successful_results = [r for r in results if r['status'] == 'success']
    sorted_results = sorted(successful_results, 
                          key=lambda x: len(x['procedures_found']), 
                          reverse=True)
    
    print(f"\n⭐ Enlaces más informativos:")
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"   {i}. {result['entity']} - {len(result['procedures_found'])} procedimientos")
        print(f"      {result['title'][:70]}...")
        print(f"      {result['url']}")
        print()
    
    # Guardar resultados
    report_data = {
        'analysis_date': datetime.now().isoformat(),
        'summary': {
            'total_links': total_links,
            'successful': successful,
            'errors': errors,
            'timeouts': timeouts,
            'total_procedures': total_procedures,
            'by_entity': entity_stats
        },
        'results': results
    }
    
    with open('links_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Reporte guardado en: links_analysis.json")
    
    # Mostrar algunos procedimientos encontrados
    print(f"\n📋 EJEMPLOS DE PROCEDIMIENTOS ENCONTRADOS:")
    print("-" * 45)
    
    all_procedures = []
    for result in successful_results:
        all_procedures.extend(result['procedures_found'])
    
    unique_procedures = list(set(all_procedures))[:10]
    
    for i, proc in enumerate(unique_procedures, 1):
        clean_proc = proc.strip()[:80]
        print(f"   {i:2d}. {clean_proc}")
    
    return report_data

def main():
    """Función principal"""
    
    try:
        # Procesar enlaces
        results = process_links_file()
        
        if results:
            # Generar reporte
            generate_links_report(results)
            print(f"\n🎉 Procesamiento completado exitosamente!")
        else:
            print(f"\n⚠️ No se pudieron procesar enlaces")
    
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")

if __name__ == "__main__":
    main()
