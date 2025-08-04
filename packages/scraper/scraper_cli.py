#!/usr/bin/env python3
"""
CLI para ejecutar el sistema de scraping TUPA
"""

import asyncio
import click
import sys
import os
from datetime import datetime

# Importar módulos del scraper
from src.scraping_orchestrator import ScrapingOrchestrator
from src.database_integration import DatabaseIntegration

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """🕷️ Sistema de Scraping TUPA - Extracción de datos gubernamentales"""
    pass

@cli.command()
@click.option('--save-db/--no-save-db', default=True, help='Guardar en base de datos')
@click.option('--export/--no-export', default=True, help='Exportar archivos')
@click.option('--db-url', type=str, help='URL personalizada de base de datos')
@click.option('--limit', type=int, default=50, help='Límite de procedimientos a procesar')
def scrape(save_db, export, db_url, limit):
    """Ejecutar scraping completo de procedimientos TUPA"""
    click.echo("🚀 Iniciando scraping completo...")
    
    async def run():
        orchestrator = ScrapingOrchestrator(db_url)
        
        try:
            results = await orchestrator.run_full_process(
                save_to_db=save_db,
                export_files=export
            )
            
            click.echo(f"✅ Proceso completado:")
            click.echo(f"   📊 Procedimientos scrapeados: {results['procedures_scraped']}")
            click.echo(f"   💾 Guardados en BD: {results['procedures_saved']}")
            click.echo(f"   ⏱️  Duración: {results['duration_seconds']:.2f}s")
            click.echo(f"   🏢 Entidades: {len(results['entities_processed'])}")
            
            if results['errors'] > 0:
                click.echo(f"   ⚠️  Errores: {results['errors']}", fg='yellow')
            
        except Exception as e:
            click.echo(f"❌ Error: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())

@cli.command()
@click.option('--db-url', type=str, help='URL personalizada de base de datos')
def validate(db_url):
    """Validar integridad de datos en base de datos"""
    click.echo("🔍 Validando integridad de datos...")
    
    async def run():
        orchestrator = ScrapingOrchestrator(db_url)
        
        try:
            results = await orchestrator.validate_database_integrity()
            
            click.echo(f"✅ Validación completada:")
            click.echo(f"   📊 Total procedimientos: {results.get('total_procedures', 0)}")
            click.echo(f"   🏢 Entidades: {results.get('entities_count', 0)}")
            
        except Exception as e:
            click.echo(f"❌ Error en validación: {e}", err=True)
            sys.exit(1)
    
    asyncio.run(run())

@cli.command()
@click.option('--db-url', type=str, help='URL personalizada de base de datos')
@click.argument('query', required=True)
@click.option('--limit', type=int, default=10, help='Límite de resultados')
def search(db_url, query, limit):
    """Buscar procedimientos en base de datos"""
    click.echo(f"🔍 Buscando: '{query}'...")
    
    async def run():
        db = DatabaseIntegration(db_url)
        
        try:
            await db.setup_connection()
            results = await db.search_procedures(query, limit)
            
            if results:
                click.echo(f"📋 Encontrados {len(results)} resultados:")
                for i, proc in enumerate(results, 1):
                    cost_info = f"S/{proc['cost']}" if proc['cost'] > 0 else "Gratuito"
                    online_info = "🌐" if proc['is_online'] else "🏢"
                    
                    click.echo(f"   {i}. {proc['name']}")
                    click.echo(f"      🏛️  {proc['entity']} | 💰 {cost_info} | {online_info}")
                    click.echo(f"      📝 {proc['description'][:100]}...")
                    click.echo()
            else:
                click.echo("❌ No se encontraron resultados")
                
        except Exception as e:
            click.echo(f"❌ Error en búsqueda: {e}", err=True)
            sys.exit(1)
        finally:
            await db.close_connection()
    
    asyncio.run(run())

@cli.command()
@click.option('--db-url', type=str, help='URL personalizada de base de datos')
def stats(db_url):
    """Mostrar estadísticas de base de datos"""
    click.echo("📊 Obteniendo estadísticas...")
    
    async def run():
        db = DatabaseIntegration(db_url)
        
        try:
            await db.setup_connection()
            stats = await db.get_procedures_count()
            
            click.echo(f"📈 Estadísticas de base de datos:")
            click.echo(f"   📊 Total procedimientos: {stats.get('total_procedures', 0)}")
            
            if 'by_entity' in stats:
                click.echo(f"   🏢 Por entidad:")
                for entity, count in sorted(stats['by_entity'].items()):
                    click.echo(f"      - {entity}: {count}")
                    
        except Exception as e:
            click.echo(f"❌ Error obteniendo estadísticas: {e}", err=True)
            sys.exit(1)
        finally:
            await db.close_connection()
    
    asyncio.run(run())

@cli.command()
@click.option('--format', type=click.Choice(['json', 'csv', 'both']), default='both')
@click.option('--output', type=str, help='Directorio de salida')
def export(format, output):
    """Exportar datos sin ejecutar scraping"""
    click.echo(f"📤 Exportando datos en formato {format}...")
    
    # TODO: Implementar exportación desde BD sin scraping
    click.echo("⚠️  Funcionalidad en desarrollo")

@cli.command()
def doctor():
    """Verificar configuración y dependencias del sistema"""
    click.echo("🔬 Verificando configuración del sistema...")
    
    # Verificar Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    click.echo(f"   🐍 Python: {python_version}", fg='green')
    
    # Verificar dependencias críticas
    dependencies = [
        ('beautifulsoup4', 'BeautifulSoup'),
        ('selenium', 'Selenium WebDriver'),
        ('aiohttp', 'HTTP asíncrono'),
        ('pandas', 'Procesamiento de datos'),
        ('sqlalchemy', 'Base de datos')
    ]
    
    for module, description in dependencies:
        try:
            __import__(module)
            click.echo(f"   ✅ {description}: Instalado", fg='green')
        except ImportError:
            click.echo(f"   ❌ {description}: No instalado", fg='red')
    
    # Verificar Chrome/Chromium
    chrome_paths = [
        '/usr/bin/google-chrome',
        '/usr/bin/chromium-browser',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    ]
    
    chrome_found = any(os.path.exists(path) for path in chrome_paths)
    if chrome_found:
        click.echo(f"   ✅ Chrome/Chromium: Encontrado", fg='green')
    else:
        click.echo(f"   ⚠️  Chrome/Chromium: No encontrado (requerido para Selenium)", fg='yellow')
    
    # Verificar archivos de configuración
    config_files = ['requirements.txt', 'src/tupa_scraper.py', 'src/database_integration.py']
    for file in config_files:
        if os.path.exists(file):
            click.echo(f"   ✅ {file}: Presente", fg='green')
        else:
            click.echo(f"   ❌ {file}: Faltante", fg='red')
    
    click.echo("\n🎯 Sistema listo para ejecutar scraping!" if chrome_found else "\n⚠️  Instalar Chrome/Chromium antes de continuar")

if __name__ == '__main__':
    # Configurar event loop para Windows si es necesario
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    cli()
