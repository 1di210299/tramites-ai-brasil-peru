"""
Middleware para logging de requests
"""

import time
import logging
from fastapi import Request
import uuid

# Configurar logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    """Middleware para loggear requests y responses"""
    
    # Generar ID único para la request
    request_id = str(uuid.uuid4())[:8]
    
    # Obtener información de la request
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0]
    
    user_agent = request.headers.get("user-agent", "Unknown")
    method = request.method
    url = str(request.url)
    
    # Log de inicio
    start_time = time.time()
    logger.info(
        f"[{request_id}] {method} {url} - IP: {client_ip} - "
        f"User-Agent: {user_agent}"
    )
    
    # Procesar request
    try:
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        
        # Log de finalización
        logger.info(
            f"[{request_id}] {method} {url} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )
        
        # Agregar headers de timing
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as exc:
        # Log de error
        process_time = time.time() - start_time
        logger.error(
            f"[{request_id}] {method} {url} - "
            f"Error: {type(exc).__name__}: {str(exc)} - "
            f"Time: {process_time:.3f}s"
        )
        raise exc
