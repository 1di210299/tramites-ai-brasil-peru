# Tramites AI Perú 🇵🇪

Asistente virtual de IA para trámites y formalización en Perú. Simplifica procesos burocráticos con inteligencia artificial, generación automática de documentos y orientación paso a paso.

## 🎯 Visión

Democratizar el acceso a información clara y precisa sobre trámites gubernamentales en Perú, eliminando barreras de tiempo y conocimiento técnico mediante IA conversacional.

## 🚀 Características

- **Chat Inteligente**: Consulta cualquier trámite en lenguaje natural
- **Generación de Documentos**: PDFs automáticos de solicitudes y cartas
- **Base de Datos TUPA**: Información actualizada de procedimientos oficiales
- **Búsqueda Semántica**: Encuentra trámites relacionados con embeddings
- **Sistema de Pago**: Acceso premium con Stripe/Culqi
- **Multicanal**: Web y WhatsApp

## 🏗️ Arquitectura

```
tramites-ai-peru/
├── apps/
│   ├── frontend/        # Next.js + React UI
│   └── backend/         # Node.js API + Express
├── packages/
│   ├── scraper/         # Scripts TUPA scraping
│   ├── shared/          # Tipos TypeScript compartidos
│   └── database/        # Esquemas y migraciones
└── infra/               # Docker + deployment
```

## 🎯 Trámites Soportados (MVP)

1. Duplicado de DNI
2. Renovación de DNI
3. Inscripción RUC SUNAT
4. Licencia de funcionamiento municipal
5. Certificado de antecedentes penales
6. Inscripción en registros públicos
7. Permiso de trabajo para extranjeros
8. Certificado de discapacidad
9. Licencia de conducir
10. Registro de marca

## 🛠️ Tecnologías

- **Frontend**: Next.js 14, React, TailwindCSS, Shadcn/ui
- **Backend**: Node.js, Express, TypeScript
- **Base de Datos**: PostgreSQL + Prisma ORM
- **IA**: OpenAI GPT-4, embeddings vectoriales
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

### Q1 2025 - MVP
- [x] Chat básico con GPT
- [x] Scraping TUPA inicial
- [x] Generación PDF
- [x] Sistema de pagos
- [ ] Deploy producción

### Q2 2025 - Expansión
- [ ] Integración WhatsApp
- [ ] 50+ trámites nuevos
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
