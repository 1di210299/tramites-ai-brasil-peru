"""
Middleware para rate limiting
"""

import time
from fastapi import Request, HTTPException, status
from core.redis import RedisCache
from core.config import settings
import json

async def rate_limiter_middleware(request: Request, call_next):
    """Middleware para limitar tasa de requests"""
    
    # Obtener IP del cliente
    client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0]
    
    # Clave de rate limiting
    cache_key = f"rate_limit:{client_ip}"
    
    # Obtener contador actual
    current_count = await RedisCache.get(cache_key)
    
    if current_count:
        count_data = json.loads(current_count)
        request_count = count_data.get("count", 0)
        window_start = count_data.get("window_start", time.time())
        
        # Verificar si estamos en la misma ventana de tiempo
        if time.time() - window_start < settings.RATE_LIMIT_WINDOW:
            if request_count >= settings.RATE_LIMIT_REQUESTS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Límite de {settings.RATE_LIMIT_REQUESTS} requests por {settings.RATE_LIMIT_WINDOW} segundos excedido",
                        "retry_after": settings.RATE_LIMIT_WINDOW - (time.time() - window_start)
                    }
                )
            
            # Incrementar contador
            new_count_data = {
                "count": request_count + 1,
                "window_start": window_start
            }
        else:
            # Nueva ventana de tiempo
            new_count_data = {
                "count": 1,
                "window_start": time.time()
            }
    else:
        # Primera request
        new_count_data = {
            "count": 1,
            "window_start": time.time()
        }
    
    # Guardar contador actualizado
    await RedisCache.set(
        cache_key, 
        json.dumps(new_count_data), 
        expire=settings.RATE_LIMIT_WINDOW
    )
    
    # Proceder con la request
    response = await call_next(request)
    
    # Agregar headers de rate limiting
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(
        max(0, settings.RATE_LIMIT_REQUESTS - new_count_data["count"])
    )
    response.headers["X-RateLimit-Reset"] = str(
        int(new_count_data["window_start"] + settings.RATE_LIMIT_WINDOW)
    )
    
    return response
