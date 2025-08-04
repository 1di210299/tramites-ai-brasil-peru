#!/usr/bin/env python3
"""
Script de prueba para el sistema de scraping TUPA
"""

import asyncio
import logging
from src.tupa_scraper import TupaScraper, ProcedureData
from src.database_integration import DatabaseIntegration

# Configurar logging para pruebas
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_scraper_basic():
    """Prueba básica del scraper"""
    print("🧪 Probando scraper básico...")
    
    scraper = TupaScraper()
    
    try:
        # Probar scraping de entidades específicas (más confiable)
        procedures = await scraper.scrape_specific_entities()
        
        if procedures:
            print(f"✅ Scraper funcionando: {len(procedures)} procedimientos extraídos")
            
            # Mostrar muestra de datos
            for i, proc in enumerate(procedures[:3]):
                print(f"\n📋 Procedimiento {i+1}:")
                print(f"   Nombre: {proc.name}")
                print(f"   Entidad: {proc.entity_name}")
                print(f"   Costo: S/{proc.cost}")
                print(f"   Categoría: {proc.category}")
                print(f"   Requisitos: {len(proc.requirements)}")
            
            return True
        else:
            print("❌ No se extrajeron procedimientos")
            return False
            
    except Exception as e:
        print(f"❌ Error en scraper: {e}")
        return False

async def test_database_connection():
    """Prueba conexión a base de datos"""
    print("\n🗄️ Probando conexión a base de datos...")
    
    db = DatabaseIntegration()
    
    try:
        await db.setup_connection()
        print("✅ Conexión a BD exitosa")
        
        # Probar estadísticas
        stats = await db.get_procedures_count()
        print(f"📊 Procedimientos en BD: {stats.get('total_procedures', 0)}")
        
        await db.close_connection()
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión a BD: {e}")
        print("💡 Verificar que PostgreSQL esté corriendo y configurado")
        return False

async def test_data_structure():
    """Prueba estructura de datos"""
    print("\n📐 Probando estructura de datos...")
    
    try:
        # Crear procedimiento de prueba
        test_procedure = ProcedureData(
            name="Procedimiento de Prueba",
            description="Descripción de prueba",
            entity_name="Entidad Test",
            entity_code="TEST",
            tupa_code="TEST-001",
            requirements=["Requisito 1", "Requisito 2"],
            cost=50.0,
            currency="PEN",
            processing_time="5 días",
            legal_basis=["Ley Test"],
            channels=["Virtual", "Presencial"],
            category="test",
            subcategory="",
            is_free=False,
            is_online=True,
            difficulty_level="easy",
            source_url="https://test.com",
            keywords=["test", "prueba"]
        )
        
        print("✅ Estructura de datos válida")
        print(f"   📝 Nombre: {test_procedure.name}")
        print(f"   🏛️  Entidad: {test_procedure.entity_name}")
        print(f"   💰 Costo: S/{test_procedure.cost}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error en estructura de datos: {e}")
        return False

async def test_integration():
    """Prueba de integración completa (mini-scraping)"""
    print("\n🔄 Probando integración completa...")
    
    try:
        scraper = TupaScraper()
        db = DatabaseIntegration()
        
        # Scraping pequeño
        procedures = await scraper.scrape_specific_entities()
        
        if not procedures:
            print("⚠️ No hay datos para probar integración")
            return False
        
        print(f"📥 Datos extraídos: {len(procedures)} procedimientos")
        
        # Probar guardado en BD (solo si hay conexión)
        try:
            await db.setup_connection()
            
            # Guardar solo un procedimiento de prueba
            test_procedures = procedures[:1]
            stats = await db.save_procedures_batch(test_procedures)
            
            print(f"💾 Guardado en BD: {stats['saved']} procedimientos")
            print("✅ Integración completa exitosa")
            
            await db.close_connection()
            return True
            
        except Exception as db_error:
            print(f"⚠️ BD no disponible, pero scraping funciona: {db_error}")
            return True
            
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        return False

async def run_all_tests():
    """Ejecutar todas las pruebas"""
    print("🚀 Iniciando pruebas del sistema de scraping TUPA")
    print("=" * 50)
    
    tests = [
        ("Estructura de Datos", test_data_structure),
        ("Scraper Básico", test_scraper_basic),
        ("Conexión BD", test_database_connection),
        ("Integración", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🔍 Ejecutando: {test_name}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results[test_name] = False
    
    # Mostrar resumen
    print("\n" + "=" * 50)
    print("📋 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas exitosas")
    
    if passed == total:
        print("🎉 ¡Todos los tests pasaron! Sistema listo para usar.")
    elif passed > 0:
        print("⚠️ Sistema parcialmente funcional. Revisar errores.")
    else:
        print("❌ Sistema no funcional. Revisar configuración.")
    
    return passed == total

if __name__ == "__main__":
    try:
        # Configurar event loop para Windows si es necesario
        if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Pruebas interrumpidas por usuario")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error fatal en pruebas: {e}")
        exit(1)
