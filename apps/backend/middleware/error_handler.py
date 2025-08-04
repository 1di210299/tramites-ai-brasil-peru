"""
Middleware para manejo de errores
"""

import traceback
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware para capturar y manejar errores globalmente"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_error(request, exc)
    
    async def handle_error(self, request: Request, exc: Exception):
        """Manejar error y retornar respuesta apropiada"""
        
        error_id = id(exc)
        
        # Log del error
        logger.error(
            f"Error {error_id} en {request.method} {request.url}: "
            f"{type(exc).__name__}: {str(exc)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        # Respuesta según tipo de error
        if isinstance(exc, ValueError):
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "bad_request",
                    "message": str(exc),
                    "error_id": error_id
                }
            )
        
        elif isinstance(exc, PermissionError):
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "forbidden",
                    "message": "No tienes permisos para acceder a este recurso",
                    "error_id": error_id
                }
            )
        
        elif isinstance(exc, FileNotFoundError):
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "not_found",
                    "message": "Recurso no encontrado",
                    "error_id": error_id
                }
            )
        
        else:
            # Error interno del servidor
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "internal_server_error",
                    "message": "Error interno del servidor. Por favor contacta al soporte.",
                    "error_id": error_id
                }
            )

async def error_handler_middleware(request: Request, call_next):
    """Función middleware para manejo de errores"""
    middleware = ErrorHandlerMiddleware(None)
    return await middleware.dispatch(request, call_next)
