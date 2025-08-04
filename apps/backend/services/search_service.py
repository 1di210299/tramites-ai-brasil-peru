"""
Servicio de búsqueda para procedimientos
"""

import asyncio
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from models import Procedure, Entity
from schemas import PaginatedResponse, Procedure as ProcedureSchema

class SearchService:
    """Servicio para búsquedas de procedimientos"""
    
    async def search_procedures(
        self,
        query: str,
        entity_id: Optional[str] = None,
        category: Optional[str] = None,
        is_free: Optional[bool] = None,
        is_online: Optional[bool] = None,
        limit: int = 10,
        offset: int = 0,
        db: AsyncSession = None
    ) -> PaginatedResponse:
        """Buscar procedimientos con filtros"""
        
        # Construir query base
        base_query = select(Procedure).options(selectinload(Procedure.entity))
        count_query = select(func.count(Procedure.id))
        
        # Filtros
        filters = [Procedure.is_active == True]
        
        # Búsqueda por texto
        if query:
            search_filter = or_(
                Procedure.name.ilike(f"%{query}%"),
                Procedure.description.ilike(f"%{query}%"),
                Procedure.tupa_code.ilike(f"%{query}%")
            )
            
            # Buscar también en keywords y tags si existen
            if hasattr(Procedure, 'keywords'):
                search_filter = or_(
                    search_filter,
                    Procedure.keywords.any(query.lower())
                )
            
            filters.append(search_filter)
        
        # Filtro por entidad
        if entity_id:
            filters.append(Procedure.entity_id == entity_id)
        
        # Filtro por categoría
        if category:
            filters.append(Procedure.category == category)
        
        # Filtro por gratuidad
        if is_free is not None:
            filters.append(Procedure.is_free == is_free)
        
        # Filtro por disponibilidad online
        if is_online is not None:
            filters.append(Procedure.is_online == is_online)
        
        # Aplicar filtros
        where_clause = and_(*filters)
        final_query = base_query.where(where_clause)
        final_count_query = count_query.where(where_clause)
        
        # Ordenamiento por relevancia
        if query:
            # Ordenar por coincidencias en nombre primero
            final_query = final_query.order_by(
                Procedure.name.ilike(f"%{query}%").desc(),
                Procedure.name
            )
        else:
            final_query = final_query.order_by(Procedure.name)
        
        # Paginación
        final_query = final_query.offset(offset).limit(limit)
        
        # Ejecutar queries
        procedures_result = await db.execute(final_query)
        procedures = procedures_result.scalars().all()
        
        total_result = await db.execute(final_count_query)
        total = total_result.scalar()
        
        # Convertir a esquemas Pydantic
        procedure_schemas = [ProcedureSchema.from_orm(p) for p in procedures]
        
        return PaginatedResponse(
            items=procedure_schemas,
            total=total,
            page=(offset // limit) + 1,
            size=limit,
            pages=(total + limit - 1) // limit
        )
    
    async def semantic_search(
        self,
        query_embedding: List[float],
        limit: int = 5,
        db: AsyncSession = None
    ) -> List[ProcedureSchema]:
        """Búsqueda semántica usando embeddings"""
        
        if not query_embedding:
            return []
        
        try:
            # Query SQL para búsqueda por similitud coseno
            # Nota: Requiere extensión pgvector en PostgreSQL
            similarity_query = text("""
                SELECT p.*, e.name as entity_name, e.code as entity_code,
                       (p.embedding <=> :query_embedding) AS similarity
                FROM procedures p
                JOIN entities e ON p.entity_id = e.id
                WHERE p.is_active = true 
                  AND p.embedding IS NOT NULL
                ORDER BY similarity ASC
                LIMIT :limit
            """)
            
            result = await db.execute(
                similarity_query, 
                {
                    "query_embedding": str(query_embedding), 
                    "limit": limit
                }
            )
            
            procedures = []
            for row in result.fetchall():
                # Crear objeto Procedure manualmente desde el resultado
                procedure_data = {
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "tupa_code": row.tupa_code,
                    "entity_id": row.entity_id,
                    "requirements": row.requirements,
                    "cost": row.cost,
                    "currency": row.currency,
                    "processing_time": row.processing_time,
                    "legal_basis": row.legal_basis,
                    "channels": row.channels,
                    "category": row.category,
                    "subcategory": row.subcategory,
                    "is_free": row.is_free,
                    "is_online": row.is_online,
                    "difficulty_level": row.difficulty_level,
                    "keywords": row.keywords,
                    "tags": row.tags,
                    "is_active": row.is_active,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    # Información de entidad
                    "entity": {
                        "id": row.entity_id,
                        "name": row.entity_name,
                        "code": row.entity_code
                    }
                }
                
                procedures.append(ProcedureSchema(**procedure_data))
            
            return procedures
            
        except Exception as e:
            print(f"Error en búsqueda semántica: {e}")
            # Fallback a búsqueda regular
            return []
    
    async def get_trending_procedures(
        self,
        limit: int = 10,
        db: AsyncSession = None
    ) -> List[ProcedureSchema]:
        """Obtener procedimientos más consultados"""
        
        from models import Query as QueryModel
        from datetime import datetime, timedelta
        
        # Últimos 30 días
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        try:
            trending_query = select(
                Procedure,
                func.count(QueryModel.id).label('query_count')
            ).join(
                QueryModel, Procedure.id == QueryModel.procedure_id
            ).where(
                and_(
                    Procedure.is_active == True,
                    QueryModel.created_at >= thirty_days_ago
                )
            ).group_by(
                Procedure.id
            ).order_by(
                func.count(QueryModel.id).desc()
            ).limit(limit)
            
            result = await db.execute(trending_query)
            procedures = [row[0] for row in result.fetchall()]
            
            return [ProcedureSchema.from_orm(p) for p in procedures]
            
        except Exception as e:
            print(f"Error obteniendo procedimientos trending: {e}")
            return []
    
    async def search_by_keywords(
        self,
        keywords: List[str],
        limit: int = 10,
        db: AsyncSession = None
    ) -> List[ProcedureSchema]:
        """Buscar por palabras clave específicas"""
        
        if not keywords:
            return []
        
        # Construir filtro para keywords
        keyword_filters = []
        for keyword in keywords:
            keyword_filters.append(
                or_(
                    Procedure.name.ilike(f"%{keyword}%"),
                    Procedure.description.ilike(f"%{keyword}%"),
                    Procedure.category.ilike(f"%{keyword}%")
                )
            )
        
        query = select(Procedure).options(
            selectinload(Procedure.entity)
        ).where(
            and_(
                Procedure.is_active == True,
                or_(*keyword_filters)
            )
        ).limit(limit)
        
        result = await db.execute(query)
        procedures = result.scalars().all()
        
        return [ProcedureSchema.from_orm(p) for p in procedures]
    
    async def get_related_procedures(
        self,
        procedure: Procedure,
        limit: int = 5,
        db: AsyncSession = None
    ) -> List[ProcedureSchema]:
        """Obtener procedimientos relacionados"""
        
        # Buscar procedimientos de la misma categoría o entidad
        related_query = select(Procedure).options(
            selectinload(Procedure.entity)
        ).where(
            and_(
                Procedure.is_active == True,
                Procedure.id != procedure.id,
                or_(
                    Procedure.category == procedure.category,
                    Procedure.entity_id == procedure.entity_id
                )
            )
        ).limit(limit)
        
        result = await db.execute(related_query)
        procedures = result.scalars().all()
        
        return [ProcedureSchema.from_orm(p) for p in procedures]
