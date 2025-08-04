#!/usr/bin/env python3
"""
Integración con base de datos para guardar datos scrapeados
"""

import asyncio
import sys
import os
from typing import List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import logging

# Agregar el backend al path para importar modelos
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../apps/backend'))

from models import Entity, Procedure
from tupa_scraper import ProcedureData

logger = logging.getLogger(__name__)

class DatabaseIntegration:
    """Integración con base de datos PostgreSQL"""
    
    def __init__(self, database_url: str = None):
        if not database_url:
            # URL por defecto para desarrollo
            database_url = "postgresql+asyncpg://postgres:password@localhost:5432/tramites_db"
        
        self.database_url = database_url
        self.engine = None
        self.AsyncSessionLocal = None
    
    async def setup_connection(self):
        """Configurar conexión a base de datos"""
        try:
            self.engine = create_async_engine(
                self.database_url,
                echo=False,
                pool_size=10,
                max_overflow=20
            )
            
            self.AsyncSessionLocal = sessionmaker(
                self.engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            logger.info("Conexión a base de datos configurada exitosamente")
            
        except Exception as e:
            logger.error(f"Error configurando conexión a BD: {e}")
            raise
    
    async def create_or_get_entity(self, session: AsyncSession, entity_name: str, entity_code: str) -> Entity:
        """Crear o obtener entidad existente"""
        try:
            # Verificar si la entidad existe
            result = await session.execute(
                select(Entity).where(Entity.code == entity_code)
            )
            entity = result.scalar_one_or_none()
            
            if not entity:
                # Crear nueva entidad
                entity = Entity(
                    name=entity_name,
                    code=entity_code,
                    sector='nacional',
                    description=f'Entidad gubernamental: {entity_name}',
                    website=self._get_entity_website(entity_code),
                    contact_info={
                        'phone': '',
                        'email': '',
                        'address': ''
                    }
                )
                session.add(entity)
                await session.flush()
                logger.info(f"Entidad creada: {entity_name}")
            
            return entity
            
        except Exception as e:
            logger.error(f"Error creando/obteniendo entidad {entity_name}: {e}")
            raise
    
    def _get_entity_website(self, entity_code: str) -> str:
        """Obtener website de entidad por código"""
        websites = {
            'SUNAT': 'https://www.sunat.gob.pe',
            'RENIEC': 'https://www.reniec.gob.pe',
            'SUNARP': 'https://www.sunarp.gob.pe',
            'MINSA': 'https://www.minsa.gob.pe',
            'MUNI': 'https://www.municap.com',
            'GOB': 'https://www.gob.pe'
        }
        return websites.get(entity_code, 'https://www.gob.pe')
    
    async def save_procedure(self, session: AsyncSession, procedure_data: ProcedureData, entity: Entity) -> Optional[Procedure]:
        """Guardar un procedimiento en la base de datos"""
        try:
            # Verificar si el procedimiento ya existe
            result = await session.execute(
                select(Procedure).where(
                    Procedure.tupa_code == procedure_data.tupa_code,
                    Procedure.entity_id == entity.id
                )
            )
            
            existing_procedure = result.scalar_one_or_none()
            
            if existing_procedure:
                logger.info(f"Procedimiento ya existe: {procedure_data.name}")
                return existing_procedure
            
            # Crear nuevo procedimiento
            procedure = Procedure(
                name=procedure_data.name,
                description=procedure_data.description,
                entity_id=entity.id,
                tupa_code=procedure_data.tupa_code,
                requirements=procedure_data.requirements,
                cost=procedure_data.cost,
                currency=procedure_data.currency,
                processing_time=procedure_data.processing_time,
                legal_basis=procedure_data.legal_basis,
                channels=procedure_data.channels,
                category=procedure_data.category,
                subcategory=procedure_data.subcategory,
                is_free=procedure_data.is_free,
                is_online=procedure_data.is_online,
                difficulty_level=procedure_data.difficulty_level,
                keywords=procedure_data.keywords,
                metadata={
                    'source_url': procedure_data.source_url,
                    'scraped_at': str(asyncio.get_event_loop().time()),
                    'scraper_version': '1.0'
                }
            )
            
            session.add(procedure)
            logger.info(f"Procedimiento guardado: {procedure_data.name}")
            return procedure
            
        except Exception as e:
            logger.error(f"Error guardando procedimiento {procedure_data.name}: {e}")
            return None
    
    async def save_procedures_batch(self, procedures_data: List[ProcedureData]) -> dict:
        """Guardar lote de procedimientos"""
        stats = {
            'total': len(procedures_data),
            'saved': 0,
            'skipped': 0,
            'errors': 0
        }
        
        if not self.AsyncSessionLocal:
            await self.setup_connection()
        
        async with self.AsyncSessionLocal() as session:
            try:
                for proc_data in procedures_data:
                    try:
                        # Crear o obtener entidad
                        entity = await self.create_or_get_entity(
                            session, 
                            proc_data.entity_name, 
                            proc_data.entity_code
                        )
                        
                        # Guardar procedimiento
                        procedure = await self.save_procedure(session, proc_data, entity)
                        
                        if procedure:
                            stats['saved'] += 1
                        else:
                            stats['skipped'] += 1
                            
                    except Exception as e:
                        logger.error(f"Error procesando {proc_data.name}: {e}")
                        stats['errors'] += 1
                        continue
                
                # Commit de toda la transacción
                await session.commit()
                logger.info(f"Batch guardado: {stats['saved']} procedimientos")
                
            except Exception as e:
                await session.rollback()
                logger.error(f"Error en batch: {e}")
                raise
        
        return stats
    
    async def get_procedures_count(self) -> dict:
        """Obtener estadísticas de procedimientos en BD"""
        if not self.AsyncSessionLocal:
            await self.setup_connection()
        
        async with self.AsyncSessionLocal() as session:
            try:
                # Total de procedimientos
                total_result = await session.execute(select(Procedure))
                total_procedures = len(total_result.all())
                
                # Por entidad
                entities_result = await session.execute(
                    select(Entity.name, Procedure.id)
                    .join(Procedure, Entity.id == Procedure.entity_id)
                )
                
                entity_counts = {}
                for entity_name, _ in entities_result.all():
                    entity_counts[entity_name] = entity_counts.get(entity_name, 0) + 1
                
                return {
                    'total_procedures': total_procedures,
                    'by_entity': entity_counts
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo estadísticas: {e}")
                return {}
    
    async def search_procedures(self, query: str, limit: int = 10) -> List[dict]:
        """Buscar procedimientos en BD"""
        if not self.AsyncSessionLocal:
            await self.setup_connection()
        
        async with self.AsyncSessionLocal() as session:
            try:
                # Búsqueda simple por nombre y descripción
                result = await session.execute(
                    select(Procedure, Entity)
                    .join(Entity, Procedure.entity_id == Entity.id)
                    .where(
                        Procedure.name.ilike(f'%{query}%') |
                        Procedure.description.ilike(f'%{query}%')
                    )
                    .limit(limit)
                )
                
                procedures = []
                for procedure, entity in result.all():
                    procedures.append({
                        'id': str(procedure.id),
                        'name': procedure.name,
                        'description': procedure.description,
                        'entity': entity.name,
                        'cost': procedure.cost,
                        'processing_time': procedure.processing_time,
                        'is_free': procedure.is_free,
                        'is_online': procedure.is_online,
                        'category': procedure.category
                    })
                
                return procedures
                
            except Exception as e:
                logger.error(f"Error en búsqueda: {e}")
                return []
    
    async def close_connection(self):
        """Cerrar conexión a base de datos"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Conexión a base de datos cerrada")

# Script de utilidad para probar la integración
async def test_database_integration():
    """Función de prueba"""
    db = DatabaseIntegration()
    
    try:
        await db.setup_connection()
        
        # Obtener estadísticas
        stats = await db.get_procedures_count()
        print(f"Estadísticas actuales: {stats}")
        
        # Buscar procedimientos
        results = await db.search_procedures("DNI")
        print(f"Resultados de búsqueda 'DNI': {len(results)}")
        for result in results:
            print(f"  - {result['name']} ({result['entity']})")
        
    finally:
        await db.close_connection()

if __name__ == "__main__":
    asyncio.run(test_database_integration())
