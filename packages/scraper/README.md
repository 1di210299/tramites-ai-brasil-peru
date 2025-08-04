# 🕷️ Scraper TUPA - Sistema de Extracción de Datos

Sistema completo de scraping para extraer y estructurar datos de procedimientos administrativos (TUPA) del gobierno peruano.

## 🎯 Características Principales

- **Scraping Asíncrono**: Utiliza `aiohttp` y `asyncio` para scraping eficiente
- **Múltiples Fuentes**: Extrae datos de gob.pe, SUNAT, RENIEC, SUNARP y otras entidades
- **Detección Anti-Bot**: Usa `undetected-chromedriver` y rotación de User-Agents
- **Integración BD**: Conexión directa con PostgreSQL usando SQLAlchemy async
- **Estructuración Inteligente**: Clasifica automáticamente procedimientos por categoría
- **Exportación Múltiple**: Genera JSON, CSV y formatos optimizados para frontend

## 🚀 Instalación y Configuración

### Prerequisitos

1. **Python 3.9+**
2. **Chrome/Chromium** (para Selenium)
3. **PostgreSQL** (para almacenamiento)

### Instalación

```bash
# Navegar al directorio del scraper
cd packages/scraper

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno (opcional)
cp .env.example .env
```

### Variables de Entorno

```bash
# Database (opcional - usa defaults si no se especifica)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/tramites_db

# Configuración de scraping
SCRAPER_DELAY=2  # Delay entre requests en segundos
SCRAPER_MAX_PAGES=50  # Máximo de páginas a procesar
SCRAPER_TIMEOUT=30  # Timeout para requests HTTP
```

## 📋 Uso del Sistema

### Scraping Completo

```bash
# Ejecutar scraping completo (recomendado)
python src/scraping_orchestrator.py --mode full

# Solo scraping sin guardar en BD
python src/scraping_orchestrator.py --mode full --no-db

# Solo scraping sin exportar archivos
python src/scraping_orchestrator.py --mode full --no-export
```

### Scraping Incremental

```bash
# Actualización incremental (solo nuevos procedimientos)
python src/scraping_orchestrator.py --mode incremental
```

### Validación de Datos

```bash
# Validar integridad de datos en BD
python src/scraping_orchestrator.py --mode validate
```

### Uso Programático

```python
from src.scraping_orchestrator import ScrapingOrchestrator

# Crear orchestrador
orchestrator = ScrapingOrchestrator()

# Ejecutar proceso completo
results = await orchestrator.run_full_process()

print(f"Procedimientos scrapeados: {results['procedures_scraped']}")
print(f"Guardados en BD: {results['procedures_saved']}")
```

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **`tupa_scraper.py`**: Scraper principal con lógica de extracción
2. **`database_integration.py`**: Integración con PostgreSQL
3. **`scraping_orchestrator.py`**: Orchestrador que coordina todo el proceso

### Flujo de Trabajo

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Scraping      │───▶│   Estructuración │───▶│  Almacenamiento │
│   Web Sites     │    │   y Validación   │    │   PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ gob.pe, SUNAT   │    │ Clasificación    │    │ Exportación     │
│ RENIEC, SUNARP  │    │ Categorización   │    │ JSON, CSV       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Datos Extraídos

Para cada procedimiento se extrae:

- **Información Básica**: Nombre, descripción, entidad responsable
- **Detalles Técnicos**: Código TUPA, requisitos, costo, tiempo de procesamiento
- **Clasificación**: Categoría, dificultad, disponibilidad online
- **Metadatos**: URL fuente, palabras clave, base legal

### Entidades Cubiertas

- **SUNAT**: Trámites tributarios, RUC, declaraciones
- **RENIEC**: DNI, pasaportes, documentos de identidad
- **SUNARP**: Registros públicos, empresas, propiedades
- **MINSA**: Trámites de salud, certificados médicos
- **Municipalidades**: Licencias, funcionamiento, construcción

### Categorías de Procedimientos

- `identidad`: Documentos de identificación
- `empresarial`: Constitución y gestión de empresas
- `tributario`: Impuestos y obligaciones fiscales
- `vehicular`: Licencias de conducir, vehículos
- `educacion`: Títulos, certificados educativos
- `salud`: Trámites médicos y sanitarios
- `laboral`: Empleo y relaciones laborales
- `municipal`: Trámites municipales y locales

## 📁 Archivos Generados

### JSON Completo
```json
{
  "name": "Duplicado de DNI por Deterioro",
  "description": "Obtención de un nuevo DNI cuando el documento se encuentra deteriorado",
  "entity_name": "RENIEC",
  "entity_code": "RENIEC",
  "tupa_code": "RENIEC-001",
  "requirements": ["DNI deteriorado original", "Recibo de pago"],
  "cost": 32.20,
  "currency": "PEN",
  "processing_time": "48 horas",
  "category": "identidad",
  "is_free": false,
  "is_online": false,
  "difficulty_level": "easy"
}
```

### JSON para Frontend
```json
{
  "metadata": {
    "total_procedures": 150,
    "last_updated": "2024-01-15T10:30:00",
    "entities": ["SUNAT", "RENIEC", "SUNARP"],
    "categories": ["identidad", "empresarial", "tributario"]
  },
  "procedures": [...]
}
```

### CSV para Análisis
```csv
Nombre,Entidad,Categoria,Costo,Es_Gratuito,Es_Online,Dificultad
Duplicado de DNI,RENIEC,identidad,32.20,False,False,easy
Inscripción RUC,SUNAT,tributario,0.00,True,True,easy
```

## 🔧 Configuración Avanzada

### Personalizar Scraping

```python
# En tupa_scraper.py, modificar configuración
class TupaScraper:
    def __init__(self):
        self.base_urls = {
            'custom_entity': 'https://custom-entity.gob.pe'
        }
        
        # Agregar nueva categoría
        self.categories['nueva_categoria'] = ['keyword1', 'keyword2']
```

### Extender Entidades

```python
async def _scrape_custom_entity(self) -> List[ProcedureData]:
    """Scraper específico para entidad personalizada"""
    procedures = []
    
    # Implementar lógica específica
    custom_data = [
        {
            'name': 'Procedimiento Custom',
            'description': 'Descripción del procedimiento',
            # ... más campos
        }
    ]
    
    for data in custom_data:
        procedure = ProcedureData(**data)
        procedures.append(procedure)
    
    return procedures
```

## 📈 Monitoreo y Logging

### Logs Generados

- `scraping.log`: Log detallado del proceso
- `scraping_report.txt`: Reporte final con estadísticas
- Salida en consola con progreso en tiempo real

### Métricas Disponibles

```python
results = {
    'procedures_scraped': 150,
    'procedures_saved': 145,
    'errors': 5,
    'entities_processed': {'SUNAT', 'RENIEC', 'SUNARP'},
    'duration_seconds': 120.5
}
```

## 🐛 Troubleshooting

### Errores Comunes

1. **Chrome Driver Error**
   ```bash
   # Instalar Chrome/Chromium
   # Ubuntu/Debian
   sudo apt-get install chromium-browser
   
   # macOS
   brew install --cask google-chrome
   ```

2. **Database Connection Error**
   ```bash
   # Verificar PostgreSQL está corriendo
   # Verificar credenciales en DATABASE_URL
   # Crear base de datos si no existe
   ```

3. **Rate Limiting/Blocking**
   ```python
   # Aumentar delays en configuración
   SCRAPER_DELAY=5  # Aumentar delay entre requests
   ```

### Debug Mode

```bash
# Ejecutar con logging detallado
python -u src/scraping_orchestrator.py --mode full 2>&1 | tee debug.log
```

## 🤝 Contribuir

1. Fork del repositorio
2. Crear rama para feature: `git checkout -b feature/nueva-entidad`
3. Implementar cambios
4. Agregar tests si es necesible
5. Commit: `git commit -am 'Add nueva entidad scraper'`
6. Push: `git push origin feature/nueva-entidad`
7. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte y preguntas:
- Crear issue en GitHub
- Revisar logs en `scraping.log`
- Verificar configuración de base de datos

---

## 🎯 Próximas Funcionalidades

- [ ] Scraping inteligente con ML para detectar nuevos patrones
- [ ] API REST para ejecutar scraping bajo demanda
- [ ] Dashboard web para monitoreo en tiempo real
- [ ] Notificaciones automáticas de nuevos procedimientos
- [ ] Integración con sistemas de caché (Redis)
- [ ] Scraping diferencial (solo cambios)
- [ ] Soporte para más formatos de exportación (Excel, XML)
- [ ] Análisis de sentimientos en descripciones de procedimientos
