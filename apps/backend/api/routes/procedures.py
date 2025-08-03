"""
Rutas para búsqueda y gestión de procedimientos
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional

from core.database import get_db
from models import Procedure, Entity, User
from schemas import (
    Procedure as ProcedureSchema, 
    ProcedureSearch, 
    PaginatedResponse,
    ApiResponse
)
from api.routes.auth import get_current_user
from services.ai_service import AIService
from services.search_service import SearchService

router = APIRouter()

@router.get("/search", response_model=PaginatedResponse)
async def search_procedures(
    q: str = Query(..., description="Término de búsqueda"),
    entity_id: Optional[str] = None,
    category: Optional[str] = None,
    is_free: Optional[bool] = None,
    is_online: Optional[bool] = None,
    limit: int = Query(10, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Buscar procedimientos con filtros"""
    
    # Usar servicio de búsqueda con IA
    search_service = SearchService()
    results = await search_service.search_procedures(
        query=q,
        entity_id=entity_id,
        category=category,
        is_free=is_free,
        is_online=is_online,
        limit=limit,
        offset=offset,
        db=db
    )
    
    return results

@router.get("/semantic-search", response_model=List[ProcedureSchema])
async def semantic_search(
    query: str = Query(..., description="Consulta en lenguaje natural"),
    limit: int = Query(5, le=20),
    db: AsyncSession = Depends(get_db)
):
    """Búsqueda semántica usando embeddings"""
    
    ai_service = AIService()
    search_service = SearchService()
    
    # Generar embedding de la consulta
    query_embedding = await ai_service.generate_embedding(query)
    
    # Buscar procedimientos similares
    results = await search_service.semantic_search(
        query_embedding=query_embedding,
        limit=limit,
        db=db
    )
    
    return results

@router.get("/categories", response_model=List[str])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Obtener todas las categorías disponibles"""
    
    result = await db.execute(
        select(Procedure.category).distinct().where(
            and_(
                Procedure.category.isnot(None),
                Procedure.is_active == True
            )
        )
    )
    categories = [row[0] for row in result.fetchall() if row[0]]
    return sorted(categories)

@router.get("/entities", response_model=List[dict])
async def get_entities(db: AsyncSession = Depends(get_db)):
    """Obtener todas las entidades con conteo de procedimientos"""
    
    result = await db.execute(
        select(
            Entity.id,
            Entity.name,
            Entity.code,
            Entity.sector,
            func.count(Procedure.id).label("procedure_count")
        ).join(
            Procedure, Entity.id == Procedure.entity_id
        ).where(
            and_(
                Entity.is_active == True,
                Procedure.is_active == True
            )
        ).group_by(
            Entity.id, Entity.name, Entity.code, Entity.sector
        ).order_by(Entity.name)
    )
    
    entities = []
    for row in result.fetchall():
        entities.append({
            "id": str(row.id),
            "name": row.name,
            "code": row.code,
            "sector": row.sector,
            "procedure_count": row.procedure_count
        })
    
    return entities

@router.get("/{procedure_id}", response_model=ProcedureSchema)
async def get_procedure(
    procedure_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Obtener detalles de un procedimiento específico"""
    
    result = await db.execute(
        select(Procedure).where(
            and_(
                Procedure.id == procedure_id,
                Procedure.is_active == True
            )
        )
    )
    procedure = result.scalar_one_or_none()
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado"
        )
    
    return procedure

@router.get("/{procedure_id}/similar", response_model=List[ProcedureSchema])
async def get_similar_procedures(
    procedure_id: str,
    limit: int = Query(5, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Obtener procedimientos similares"""
    
    # Obtener el procedimiento base
    result = await db.execute(
        select(Procedure).where(Procedure.id == procedure_id)
    )
    base_procedure = result.scalar_one_or_none()
    
    if not base_procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado"
        )
    
    search_service = SearchService()
    
    if base_procedure.embedding:
        # Usar embedding existente para búsqueda semántica
        similar = await search_service.semantic_search(
            query_embedding=base_procedure.embedding,
            limit=limit + 1,  # +1 para excluir el mismo procedimiento
            db=db
        )
        # Filtrar el procedimiento actual
        similar = [p for p in similar if str(p.id) != procedure_id][:limit]
    else:
        # Buscar por categoría y entidad
        result = await db.execute(
            select(Procedure).where(
                and_(
                    Procedure.id != procedure_id,
                    or_(
                        Procedure.category == base_procedure.category,
                        Procedure.entity_id == base_procedure.entity_id
                    ),
                    Procedure.is_active == True
                )
            ).limit(limit)
        )
        similar = result.scalars().all()
    
    return similar

@router.post("/{procedure_id}/favorite", response_model=ApiResponse)
async def toggle_favorite(
    procedure_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Marcar/desmarcar procedimiento como favorito"""
    
    # Verificar que el procedimiento existe
    result = await db.execute(
        select(Procedure).where(Procedure.id == procedure_id)
    )
    procedure = result.scalar_one_or_none()
    
    if not procedure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procedimiento no encontrado"
        )
    
    # TODO: Implementar sistema de favoritos en modelo User
    return ApiResponse(
        success=True,
        message="Funcionalidad de favoritos próximamente"
    )
