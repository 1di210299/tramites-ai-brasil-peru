#!/usr/bin/env python3
"""
Procesador específico para archivos Excel (.xlsx)
"""

import pandas as pd
import json
import re
from pathlib import Path
from datetime import datetime

def analyze_excel_content(excel_path):
    """Analizar contenido de un archivo Excel específico"""
    
    content_info = {
        'file_name': excel_path.name,
        'sheets': [],
        'total_rows': 0,
        'procedures_found': [],
        'entities_mentioned': [],
        'document_type': 'EXCEL',
        'locations_found': [],
        'contact_info': []
    }
    
    try:
        print(f"   📊 Leyendo archivo Excel: {excel_path.name}")
        
        # Leer todas las hojas del Excel
        excel_file = pd.ExcelFile(excel_path)
        
        print(f"   📄 Hojas encontradas: {len(excel_file.sheet_names)}")
        
        for sheet_name in excel_file.sheet_names:
            print(f"   📋 Procesando hoja: {sheet_name}")
            
            try:
                # Leer la hoja
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                
                sheet_info = {
                    'name': sheet_name,
                    'rows': len(df),
                    'columns': len(df.columns),
                    'column_names': list(df.columns),
                    'procedures_in_sheet': [],
                    'locations_in_sheet': [],
                    'contacts_in_sheet': []
                }
                
                content_info['total_rows'] += len(df)
                
                # Convertir DataFrame a texto para análisis
                text_content = ""
                
                # Agregar nombres de columnas
                text_content += " ".join(str(col) for col in df.columns) + " "
                
                # Agregar contenido de celdas (solo primeras 1000 filas para evitar sobrecarga)
                sample_df = df.head(1000)
                for _, row in sample_df.iterrows():
                    row_text = " ".join(str(cell) for cell in row if pd.notna(cell))
                    text_content += row_text + " "
                
                # Análisis de contenido
                text_lower = text_content.lower()
                
                # Buscar procedimientos/servicios
                procedure_patterns = [
                    r'[a-záéíóúñ\s]{10,}(?:procedimiento|trámite|servicio|solicitud|registro|certificado|licencia|permiso|autorización|inscripción|renovación|duplicado|canje)[a-záéíóúñ\s]{0,20}',
                    r'[a-záéíóúñ\s]{0,20}(?:emisión|expedición|otorgamiento|gestión|atención)[a-záéíóúñ\s]{10,50}',
                ]
                
                for pattern in procedure_patterns:
                    matches = re.findall(pattern, text_lower, re.IGNORECASE)
                    clean_matches = [match.strip() for match in matches if len(match.strip()) > 15]
                    sheet_info['procedures_in_sheet'].extend(clean_matches[:5])
                
                # Buscar ubicaciones (específico para archivos de RENIEC)
                location_patterns = [
                    r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]{5,30}(?:lima|arequipa|cusco|trujillo|chiclayo|piura|iquitos|huancayo|tacna|puno|ica|ayacucho|cajamarca|huánuco|pucallpa|chimbote|sullana|juliaca|tumbes|moyobamba)',
                    r'(?:jr\.|av\.|calle|psje\.|prol\.)\s+[a-záéíóúñ\s\d]{10,50}',
                    r'(?:distrito|provincia|región|departamento)\s+[a-záéíóúñ\s]{5,30}'
                ]
                
                for pattern in location_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    clean_matches = [match.strip() for match in matches if len(match.strip()) > 8]
                    sheet_info['locations_in_sheet'].extend(clean_matches[:10])
                
                # Buscar información de contacto
                contact_patterns = [
                    r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Teléfonos
                    r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b',  # Emails
                    r'(?:lunes|martes|miércoles|jueves|viernes|sábado|domingo).*?(?:\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm))',  # Horarios
                ]
                
                for pattern in contact_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    sheet_info['contacts_in_sheet'].extend(matches[:5])
                
                content_info['sheets'].append(sheet_info)
                
                # Agregar a totales
                content_info['procedures_found'].extend(sheet_info['procedures_in_sheet'])
                content_info['locations_found'].extend(sheet_info['locations_in_sheet'])
                content_info['contact_info'].extend(sheet_info['contacts_in_sheet'])
                
                print(f"     • {sheet_info['rows']} filas, {sheet_info['columns']} columnas")
                print(f"     • {len(sheet_info['procedures_in_sheet'])} procedimientos encontrados")
                print(f"     • {len(sheet_info['locations_in_sheet'])} ubicaciones encontradas")
                
            except Exception as e:
                print(f"     ⚠️ Error procesando hoja {sheet_name}: {e}")
        
        # Detectar tipo de contenido basado en nombre de archivo
        filename_lower = excel_path.name.lower()
        if 'reniec' in filename_lower:
            content_info['entities_mentioned'].append('RENIEC')
        if 'centros' in filename_lower or 'atencion' in filename_lower:
            content_info['document_type'] = 'CENTROS_ATENCION'
        
        print(f"   ✅ Procesado: {len(content_info['sheets'])} hojas, {content_info['total_rows']} filas totales")
        
    except Exception as e:
        print(f"   ❌ Error procesando Excel: {e}")
        content_info['error'] = str(e)
    
    return content_info

def process_excel_files():
    """Procesar todos los archivos Excel"""
    
    print("📊 PROCESANDO ARCHIVOS EXCEL")
    print("=" * 50)
    
    docs_path = Path("/Users/juandiegogutierrezcortez/tramites-ai-brasil-peru/docs")
    
    if not docs_path.exists():
        print(f"❌ Directorio no encontrado: {docs_path}")
        return []
    
    # Buscar archivos Excel
    excel_files = list(docs_path.glob("*.xlsx")) + list(docs_path.glob("*.xls"))
    
    if not excel_files:
        print("❌ No se encontraron archivos Excel")
        return []
    
    print(f"📄 Encontrados {len(excel_files)} archivos Excel")
    print("-" * 30)
    
    results = []
    
    for i, excel_file in enumerate(excel_files, 1):
        print(f"\n{i}. Procesando: {excel_file.name}")
        
        try:
            size_mb = excel_file.stat().st_size / (1024 * 1024)
            print(f"   📊 Tamaño: {size_mb:.2f} MB")
            
            # Analizar contenido
            content_info = analyze_excel_content(excel_file)
            
            results.append(content_info)
            print("   ✅ Completado")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return results

def generate_excel_report(results):
    """Generar reporte de archivos Excel procesados"""
    
    print("\n📊 REPORTE DE ARCHIVOS EXCEL")
    print("=" * 40)
    
    if not results:
        print("❌ No hay resultados para reportar")
        return
    
    # Estadísticas generales
    total_files = len(results)
    total_sheets = sum(len(r['sheets']) for r in results)
    total_rows = sum(r['total_rows'] for r in results)
    total_procedures = sum(len(r['procedures_found']) for r in results)
    total_locations = sum(len(r['locations_found']) for r in results)
    
    print(f"📄 Total de archivos Excel: {total_files}")
    print(f"📄 Total de hojas: {total_sheets}")
    print(f"📊 Total de filas: {total_rows}")
    print(f"📋 Procedimientos encontrados: {total_procedures}")
    print(f"📍 Ubicaciones encontradas: {total_locations}")
    
    # Detalles por archivo
    print(f"\n📋 DETALLES POR ARCHIVO:")
    print("-" * 40)
    
    for result in results:
        print(f"\n📁 {result['file_name']}")
        print(f"   📄 Hojas: {len(result['sheets'])}")
        print(f"   📊 Filas totales: {result['total_rows']}")
        print(f"   📋 Procedimientos: {len(result['procedures_found'])}")
        print(f"   📍 Ubicaciones: {len(result['locations_found'])}")
        print(f"   📞 Contactos: {len(result['contact_info'])}")
        
        if result['entities_mentioned']:
            print(f"   🏛️ Entidades: {', '.join(result['entities_mentioned'])}")
        
        # Mostrar algunas hojas
        if result['sheets']:
            print(f"   📄 Hojas:")
            for sheet in result['sheets'][:3]:  # Solo primeras 3
                print(f"      • {sheet['name']}: {sheet['rows']} filas, {sheet['columns']} columnas")
    
    # Guardar reporte detallado
    report_data = {
        'analysis_date': datetime.now().isoformat(),
        'summary': {
            'total_files': total_files,
            'total_sheets': total_sheets,
            'total_rows': total_rows,
            'total_procedures': total_procedures,
            'total_locations': total_locations
        },
        'files': results
    }
    
    with open('excel_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Reporte guardado en: excel_analysis.json")
    
    # Mostrar algunas ubicaciones encontradas
    if total_locations > 0:
        print(f"\n📍 EJEMPLOS DE UBICACIONES ENCONTRADAS:")
        print("-" * 45)
        
        all_locations = []
        for result in results:
            all_locations.extend(result['locations_found'])
        
        unique_locations = list(set(all_locations))[:15]
        
        for i, location in enumerate(unique_locations, 1):
            clean_location = location.strip()[:70]
            print(f"   {i:2d}. {clean_location}")
    
    # Mostrar algunos procedimientos encontrados
    if total_procedures > 0:
        print(f"\n📋 EJEMPLOS DE PROCEDIMIENTOS ENCONTRADOS:")
        print("-" * 45)
        
        all_procedures = []
        for result in results:
            all_procedures.extend(result['procedures_found'])
        
        unique_procedures = list(set(all_procedures))[:10]
        
        for i, proc in enumerate(unique_procedures, 1):
            clean_proc = proc.strip()[:80]
            print(f"   {i:2d}. {clean_proc}")
    
    return report_data

def main():
    """Función principal"""
    
    try:
        # Procesar archivos Excel
        results = process_excel_files()
        
        if results:
            # Generar reporte
            generate_excel_report(results)
            print(f"\n🎉 Procesamiento de Excel completado exitosamente!")
        else:
            print(f"\n⚠️ No se pudieron procesar archivos Excel")
    
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {e}")

if __name__ == "__main__":
    main()
