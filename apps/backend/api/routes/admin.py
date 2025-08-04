"""
Rutas de administración
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta

from core.database import get_db
from models import User, Procedure, Entity, Query as QueryModel, Payment as PaymentModel
from schemas import AdminStats, ApiResponse
from api.routes.auth import get_current_user

router = APIRouter()

async def verify_admin(current_user: User = Depends(get_current_user)):
    """Verificar que el usuario es administrador"""
    # TODO: Agregar campo is_admin al modelo User
    admin_emails = ["admin@tramitesai.pe", "juandiego@tramitesai.pe"]
    
    if current_user.email not in admin_emails:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requieren permisos de administrador."
        )
    
    return current_user

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener estadísticas del sistema"""
    
    # Contar usuarios totales
    result = await db.execute(select(func.count(User.id)))
    total_users = result.scalar()
    
    # Contar procedimientos totales
    result = await db.execute(select(func.count(Procedure.id)))
    total_procedures = result.scalar()
    
    # Contar consultas totales
    result = await db.execute(select(func.count(QueryModel.id)))
    total_queries = result.scalar()
    
    # Contar documentos totales
    from models import Document as DocumentModel
    result = await db.execute(select(func.count(DocumentModel.id)))
    total_documents = result.scalar()
    
    # Consultas del día
    today = datetime.utcnow().date()
    result = await db.execute(
        select(func.count(QueryModel.id)).where(
            func.date(QueryModel.created_at) == today
        )
    )
    daily_queries = result.scalar()
    
    # Ingresos del mes
    this_month = datetime.utcnow().replace(day=1)
    result = await db.execute(
        select(func.sum(PaymentModel.amount)).where(
            and_(
                PaymentModel.created_at >= this_month,
                PaymentModel.status == "completed"
            )
        )
    )
    monthly_revenue = result.scalar() or 0
    
    return AdminStats(
        total_users=total_users,
        total_procedures=total_procedures,
        total_queries=total_queries,
        total_documents=total_documents,
        daily_queries=daily_queries,
        monthly_revenue=monthly_revenue
    )

@router.get("/users")
async def get_users(
    page: int = 1,
    size: int = 20,
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener lista de usuarios con paginación"""
    
    offset = (page - 1) * size
    
    # Obtener usuarios
    result = await db.execute(
        select(User).offset(offset).limit(size).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    
    # Contar total
    result = await db.execute(select(func.count(User.id)))
    total = result.scalar()
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }

@router.get("/procedures")
async def get_procedures_admin(
    page: int = 1,
    size: int = 20,
    entity_id: str = None,
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener lista de procedimientos con paginación"""
    
    offset = (page - 1) * size
    
    query = select(Procedure)
    if entity_id:
        query = query.where(Procedure.entity_id == entity_id)
    
    # Obtener procedimientos
    result = await db.execute(
        query.offset(offset).limit(size).order_by(Procedure.created_at.desc())
    )
    procedures = result.scalars().all()
    
    # Contar total
    count_query = select(func.count(Procedure.id))
    if entity_id:
        count_query = count_query.where(Procedure.entity_id == entity_id)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    return {
        "procedures": procedures,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }

@router.get("/queries")
async def get_queries_admin(
    page: int = 1,
    size: int = 20,
    user_id: str = None,
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener lista de consultas con paginación"""
    
    offset = (page - 1) * size
    
    query = select(QueryModel)
    if user_id:
        query = query.where(QueryModel.user_id == user_id)
    
    # Obtener consultas
    result = await db.execute(
        query.offset(offset).limit(size).order_by(QueryModel.created_at.desc())
    )
    queries = result.scalars().all()
    
    # Contar total
    count_query = select(func.count(QueryModel.id))
    if user_id:
        count_query = count_query.where(QueryModel.user_id == user_id)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    return {
        "queries": queries,
        "total": total,
        "page": page,
        "size": size,
        "pages": (total + size - 1) // size
    }

@router.get("/analytics")
async def get_analytics(
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Obtener analíticas detalladas"""
    
    # Consultas por día (últimos 30 días)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    result = await db.execute(
        select(
            func.date(QueryModel.created_at).label('date'),
            func.count(QueryModel.id).label('count')
        ).where(
            QueryModel.created_at >= thirty_days_ago
        ).group_by(
            func.date(QueryModel.created_at)
        ).order_by('date')
    )
    
    daily_queries = [
        {"date": row.date.isoformat(), "count": row.count}
        for row in result.fetchall()
    ]
    
    # Procedimientos más consultados
    result = await db.execute(
        select(
            Procedure.name,
            func.count(QueryModel.id).label('query_count')
        ).join(
            QueryModel, Procedure.id == QueryModel.procedure_id
        ).group_by(
            Procedure.id, Procedure.name
        ).order_by(
            func.count(QueryModel.id).desc()
        ).limit(10)
    )
    
    top_procedures = [
        {"name": row.name, "query_count": row.query_count}
        for row in result.fetchall()
    ]
    
    # Entidades más consultadas
    result = await db.execute(
        select(
            Entity.name,
            func.count(QueryModel.id).label('query_count')
        ).join(
            Procedure, Entity.id == Procedure.entity_id
        ).join(
            QueryModel, Procedure.id == QueryModel.procedure_id
        ).group_by(
            Entity.id, Entity.name
        ).order_by(
            func.count(QueryModel.id).desc()
        ).limit(10)
    )
    
    top_entities = [
        {"name": row.name, "query_count": row.query_count}
        for row in result.fetchall()
    ]
    
    return {
        "daily_queries": daily_queries,
        "top_procedures": top_procedures,
        "top_entities": top_entities
    }

@router.post("/sync-procedures", response_model=ApiResponse)
async def sync_procedures(
    admin_user: User = Depends(verify_admin)
):
    """Ejecutar sincronización de procedimientos desde fuentes externas"""
    
    # TODO: Implementar tarea de scraping asíncrona
    from services.scraper_service import ScraperService
    
    try:
        scraper_service = ScraperService()
        # Ejecutar en background con Celery
        task = scraper_service.sync_procedures_async.delay()
        
        return ApiResponse(
            success=True,
            message=f"Sincronización iniciada. Task ID: {task.id}",
            data={"task_id": task.id}
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Error iniciando sincronización: {str(e)}"
        )

@router.post("/users/{user_id}/toggle-premium", response_model=ApiResponse)
async def toggle_user_premium(
    user_id: str,
    admin_user: User = Depends(verify_admin),
    db: AsyncSession = Depends(get_db)
):
    """Activar/desactivar premium de un usuario"""
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    user.is_premium = not user.is_premium
    await db.commit()
    
    status_text = "activado" if user.is_premium else "desactivado"
    
    return ApiResponse(
        success=True,
        message=f"Premium {status_text} para {user.email}"
    )
