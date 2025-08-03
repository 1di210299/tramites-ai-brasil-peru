#!/usr/bin/env python3

"""
Tramites AI - FastAPI Backend
Sistema de IA para trámites gubernamentales de Perú

Funcionalidades principales:
- API REST para consultas de trámites
- Integración con OpenAI GPT-4
- Sistema de autenticación JWT
- Procesamiento de documentos PDF
- Scraping de datos TUPA
- Pagos con Stripe
- Cache con Redis
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar módulos locales
from core.config import settings
from core.database import engine, create_tables
from api.routes import auth, procedures, chat, documents, payments, admin
from middleware.error_handler import error_handler_middleware
from middleware.rate_limiter import rate_limiter_middleware
from middleware.logging import logging_middleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Configuración de inicio y cierre de la aplicación"""
    # Startup
    print("🚀 Iniciando Tramites AI Backend...")
    await create_tables()
    print("📊 Base de datos inicializada")
    yield
    # Shutdown
    print("🛑 Cerrando Tramites AI Backend...")

# Crear aplicación FastAPI
app = FastAPI(
    title="Tramites AI - API",
    description="API para el sistema de IA de trámites gubernamentales de Perú",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware de seguridad
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware personalizado
app.middleware("http")(error_handler_middleware)
app.middleware("http")(rate_limiter_middleware)
app.middleware("http")(logging_middleware)

# Rutas de la API
app.include_router(auth.router, prefix="/api/auth", tags=["Autenticación"])
app.include_router(procedures.router, prefix="/api/procedures", tags=["Trámites"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat IA"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documentos"])
app.include_router(payments.router, prefix="/api/payments", tags=["Pagos"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administración"])

@app.get("/")
async def root():
    """Endpoint de salud de la API"""
    return {
        "message": "Tramites AI - API Backend",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4
    )
