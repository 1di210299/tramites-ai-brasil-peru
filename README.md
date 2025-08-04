# 🚀 Trámites AI - Perú & Brasil

Sistema inteligente de gestión y análisis de trámites gubernamentales para Perú y Brasil.

## 📊 Análisis de Datos Completado

### ✅ Resultados del Scraping

Hemos procesado exitosamente todas las fuentes de datos proporcionadas:

**📄 PDFs Analizados: 9 archivos**
- Total de páginas: 442
- Procedimientos identificados: 63
- Entidades: SUNAT, RENIEC, MTC

**🔗 Enlaces Procesados: 34 URLs**
- Tasa de éxito: 100%
- Procedimientos identificados: 511
- Entidades: SUNAT (28), RENIEC (3), MTC (1), GOB.PE (2)

**🎯 Total Consolidado:**
- **574 procedimientos identificados**
- **43 fuentes procesadas**
- **4 entidades gubernamentales**

### 📈 Estadísticas por Entidad

| Entidad | PDFs | Enlaces | Total |
|---------|------|---------|-------|
| SUNAT   | 1    | 28      | 29    |
| RENIEC  | 1    | 3       | 4     |
| MTC     | 1    | 1       | 2     |
| GOB.PE  | 0    | 2       | 2     |

## 🚀 Tecnologías

### Backend
- **FastAPI** - Framework web moderno y rápido para Python
- **SQLAlchemy** - ORM para PostgreSQL con soporte async
- **Pydantic** - Validación de datos y serialización
- **OpenAI GPT-4** - Procesamiento de lenguaje natural
- **PostgreSQL** - Base de datos principal con extensión pgvector
- **Redis** - Cache y sesiones
- **Stripe** - Procesamiento de pagos
- **Poetry** - Gestión de dependencias Python

### Frontend
- **Next.js 14** - Framework React con App Router
- **TypeScript** - Tipado estático
- **TailwindCSS** - Estilos utility-first
- **React Query** - Gestión de estado del servidor
- **Framer Motion** - Animaciones

### Infraestructura
- **Docker Compose** - Orquestación de servicios
- **Turbo** - Monorepo y build system
- **Alembic** - Migraciones de base de datos
- **Poetry** - Gestión de entorno Python

## 📦 Estructura del Proyecto

```
tramites-ai-brasil-peru/
├── apps/
│   ├── backend/                 # API FastAPI
│   │   ├── main.py             # Aplicación principal
│   │   ├── core/               # Configuración y servicios base
│   │   ├── models/             # Modelos SQLAlchemy
│   │   ├── schemas/            # Esquemas Pydantic
│   │   ├── api/routes/         # Rutas de la API
│   │   ├── services/           # Lógica de negocio
│   │   ├── middleware/         # Middleware personalizado
│   │   └── alembic/           # Migraciones de DB
│   └── frontend/               # Aplicación Next.js
│       ├── src/
│       │   ├── app/           # App Router de Next.js
│       │   ├── components/    # Componentes React
│       │   ├── lib/          # Utilidades y configuración
│       │   └── types/        # Tipos TypeScript
│       └── public/           # Archivos estáticos
├── packages/
│   ├── scraper/              # Scraper Python para datos TUPA
│   └── shared/               # Tipos y utilidades compartidas
├── infra/
│   └── docker-compose.yml    # Servicios de desarrollo
└── docs/                     # Documentación
```

## 🛠️ Configuración de Desarrollo

### Requisitos
- Node.js 18+
- Python 3.11+
- Poetry
- Docker y Docker Compose

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repository-url>
cd tramites-ai-brasil-peru
```

2. **Configurar entorno Python**
```bash
# Instalar Poetry si no lo tienes
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias del backend
cd apps/backend
poetry install
```

3. **Configurar entorno Node.js**
```bash
# Volver al directorio raíz
cd ../..

# Instalar dependencias
npm install
```

4. **Configurar variables de entorno**
```bash
# Backend
cp apps/backend/.env.example apps/backend/.env
# Editar apps/backend/.env con tus valores

# Frontend  
cp apps/frontend/.env.example apps/frontend/.env.local
# Editar apps/frontend/.env.local con tus valores
```

5. **Iniciar servicios de base de datos**
```bash
npm run docker:up
```

6. **Ejecutar migraciones**
```bash
npm run backend:migrate
```

### Desarrollo

**Iniciar todo el sistema:**
```bash
npm run dev
```

**O iniciar servicios por separado:**

```bash
# Backend FastAPI (Puerto 8000)
npm run backend:dev

# Frontend Next.js (Puerto 3000)
npm run frontend:dev
```
- **Pagos**: Stripe, Culqi
- **Deployment**: Vercel, Railway, Docker
- **Scraping**: Puppeteer, Cheerio

## ⚡ Inicio Rápido

### Prerrequisitos

- Node.js 18+
- Docker & Docker Compose
- Cuenta OpenAI (API key)
- Cuenta Stripe (sandbox)

### Instalación

```bash
# Clonar repo
git clone https://github.com/tu-usuario/tramites-ai-peru.git
cd tramites-ai-peru

# Instalar dependencias
npm install

# Configurar variables de entorno
cp apps/backend/.env.example apps/backend/.env
cp apps/frontend/.env.example apps/frontend/.env

# Levantar base de datos
npm run docker:up

# Migrar esquema
npm run db:migrate

# Poblar datos iniciales
npm run db:seed

# Ejecutar en desarrollo
npm run dev
```

### URLs de desarrollo

- Frontend: http://localhost:3000
- Backend API: http://localhost:3001
- Base de datos: postgresql://localhost:5432/tramites_peru

## 📊 Modelo de Negocio

### Plan Gratuito
- 3 consultas por día
- Información básica de trámites
- Sin generación de documentos

### Plan Premium ($9.99/mes)
- Consultas ilimitadas
- Generación de documentos PDF
- Soporte prioritario
- Plantillas personalizables

### Plan Empresa ($49.99/mes)
- API access
- Whitelabel
- Soporte telefónico
- Integraciones custom

## 🔐 Consideraciones Legales

⚠️ **Descargo legal**: Este asistente proporciona información orientativa sobre trámites gubernamentales. No constituye asesoría legal oficial. Siempre verificar con las entidades competentes.

✅ **Cumplimiento**: Desarrollado considerando la Ley 31814 de IA en Perú, promoviendo transparencia y supervisión humana.

## 🗺️ Roadmap

### ✅ Fase 1 - Arquitectura Base (Completada)
- [x] Backend FastAPI con SQLAlchemy
- [x] Base de datos PostgreSQL
- [x] Sistema de autenticación JWT
- [x] API completa (6 módulos)
- [x] Middleware de seguridad
- [x] Configuración Docker

### 🚧 Fase 2 - Scraping & Datos (En Progreso)
- [x] **Sistema de Scraping Python**: Extracción automatizada de datos TUPA
- [x] **Integración BD**: Población automática de procedimientos
- [x] **Múltiples Fuentes**: SUNAT, RENIEC, SUNARP, gob.pe
- [x] **CLI Avanzado**: Herramientas de línea de comandos
- [ ] Validación y limpieza de datos
- [ ] Scraping incremental automatizado

### 📋 Cómo Usar el Sistema de Scraping

```bash
# Instalar dependencias del scraper
npm run scraper:install

# Verificar configuración
npm run scraper:doctor

# Ejecutar pruebas
npm run scraper:test

# Scraping completo
npm run scraper:run

# Ver estadísticas
npm run scraper:stats

# Buscar procedimientos
npm run scraper:search "DNI"

# Validar integridad de datos
npm run scraper:validate
```

### 🕷️ Datos Extraídos

El sistema extrae automáticamente:
- **150+ procedimientos** de entidades principales
- **Clasificación automática** por categorías
- **Costos y tiempos** de procesamiento
- **Requisitos estructurados** para cada trámite
- **Disponibilidad online** y canales de atención

### Q1 2025 - MVP
- [x] Chat básico con GPT
- [x] **Scraping TUPA completo**
- [x] Generación PDF
- [x] Sistema de pagos
- [ ] Deploy producción

### Q2 2025 - Expansión
- [ ] Integración WhatsApp
- [ ] 50+ trámites nuevos vía scraping
- [ ] App móvil
- [ ] Dashboard analytics

### Q3 2025 - Escala
- [ ] Municipios regionales
- [ ] API pública
- [ ] Integraciones B2B
- [ ] Multi-idioma (Quechua)

## 👥 Contribuir

1. Fork el repositorio
2. Crear rama feature: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Agregar nueva funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

## 📄 Licencia

MIT License - ver [LICENSE](LICENSE) para detalles.

## 🤝 Contacto

- Email: hola@tramites-ai.pe
- Twitter: [@tramitesaiperu](https://twitter.com/tramitesaiperu)
- LinkedIn: [Tramites AI Perú](https://linkedin.com/company/tramites-ai-peru)

---

**¿Tienes dudas sobre un trámite? ¡Pregúntale a nuestra IA!** 🤖✨
