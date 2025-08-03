"""
Configuración de Redis para cache y sesiones
"""

import redis.asyncio as redis
from .config import settings

# Cliente Redis
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)

async def get_redis():
    """Dependency para obtener cliente Redis"""
    return redis_client

class RedisCache:
    """Clase helper para operaciones de cache"""
    
    @staticmethod
    async def get(key: str):
        """Obtener valor del cache"""
        return await redis_client.get(key)
    
    @staticmethod
    async def set(key: str, value: str, expire: int = 3600):
        """Guardar valor en cache con TTL"""
        return await redis_client.set(key, value, ex=expire)
    
    @staticmethod
    async def delete(key: str):
        """Eliminar valor del cache"""
        return await redis_client.delete(key)
    
    @staticmethod
    async def exists(key: str):
        """Verificar si existe una key"""
        return await redis_client.exists(key)
