"""
Rutas para chat e interacción con IA
"""

import time
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.redis import RedisCache
from models import User, Query as QueryModel
from schemas import ChatMessage, ChatResponse, QueryCreate, ApiResponse
from api.routes.auth import get_current_user
from services.ai_service import AIService
from services.search_service import SearchService

router = APIRouter()

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enviar mensaje al chat de IA"""
    
    start_time = time.time()
    
    try:
        ai_service = AIService()
        search_service = SearchService()
        
        # Procesar mensaje con IA
        ai_response = await ai_service.process_chat_message(
            message=message.message,
            user_id=str(current_user.id),
            session_id=message.session_id
        )
        
        # Buscar procedimientos relacionados
        related_procedures = []
        if ai_response.get("procedures_query"):
            procedures_result = await search_service.search_procedures(
                query=ai_response["procedures_query"],
                limit=3,
                db=db
            )
            related_procedures = procedures_result.items
        
        # Calcular tiempo de respuesta
        response_time = (time.time() - start_time) * 1000
        
        # Guardar consulta en base de datos
        query = QueryModel(
            user_id=current_user.id,
            original_query=message.message,
            processed_query=ai_response.get("processed_query"),
            intent=ai_response.get("intent"),
            ai_response=ai_response["response"],
            confidence_score=ai_response.get("confidence", 0.8),
            response_time=response_time,
            session_id=message.session_id or str(uuid.uuid4())
        )
        
        db.add(query)
        await db.commit()
        
        return ChatResponse(
            response=ai_response["response"],
            procedures=related_procedures,
            confidence=ai_response.get("confidence", 0.8),
            response_time=response_time,
            suggestions=ai_response.get("suggestions", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando mensaje: {str(e)}"
        )

@router.get("/history")
async def get_chat_history(
    session_id: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener historial de chat del usuario"""
    
    from sqlalchemy import select, desc
    
    query = select(QueryModel).where(QueryModel.user_id == current_user.id)
    
    if session_id:
        query = query.where(QueryModel.session_id == session_id)
    
    query = query.order_by(desc(QueryModel.created_at)).limit(limit)
    
    result = await db.execute(query)
    history = result.scalars().all()
    
    # Formatear historial para el chat
    messages = []
    for q in reversed(history):  # Orden cronológico
        messages.extend([
            {
                "role": "user",
                "content": q.original_query,
                "timestamp": q.created_at.isoformat(),
                "query_id": str(q.id)
            },
            {
                "role": "assistant", 
                "content": q.ai_response,
                "timestamp": q.created_at.isoformat(),
                "confidence": q.confidence_score,
                "response_time": q.response_time
            }
        ])
    
    return {"messages": messages}

@router.post("/feedback", response_model=ApiResponse)
async def submit_feedback(
    query_id: str,
    rating: int,
    feedback: Optional[str] = None,
    was_helpful: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enviar feedback sobre una respuesta de IA"""
    
    from sqlalchemy import select, update
    
    # Verificar que la consulta pertenece al usuario
    result = await db.execute(
        select(QueryModel).where(
            QueryModel.id == query_id,
            QueryModel.user_id == current_user.id
        )
    )
    query = result.scalar_one_or_none()
    
    if not query:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consulta no encontrada"
        )
    
    # Actualizar feedback
    await db.execute(
        update(QueryModel).where(QueryModel.id == query_id).values(
            user_rating=rating,
            user_feedback=feedback,
            was_helpful=was_helpful
        )
    )
    await db.commit()
    
    return ApiResponse(
        success=True,
        message="Feedback registrado exitosamente"
    )

@router.get("/suggestions")
async def get_suggestions(
    current_user: User = Depends(get_current_user)
):
    """Obtener sugerencias de consultas populares"""
    
    # Cache de sugerencias
    cache_key = "chat_suggestions"
    cached_suggestions = await RedisCache.get(cache_key)
    
    if cached_suggestions:
        import json
        return {"suggestions": json.loads(cached_suggestions)}
    
    # Sugerencias predefinidas
    suggestions = [
        "¿Cómo saco mi DNI por primera vez?",
        "¿Qué requisitos necesito para una licencia de conducir?",
        "¿Cómo registro mi empresa en SUNARP?",
        "¿Qué documentos necesito para un pasaporte?",
        "¿Cómo obtengo un certificado de antecedentes penales?",
        "¿Cuáles son los pasos para constituir una empresa?",
        "¿Cómo actualizo mis datos en RENIEC?",
        "¿Qué trámites necesito para importar productos?"
    ]
    
    # Guardar en cache por 1 hora
    import json
    await RedisCache.set(cache_key, json.dumps(suggestions), expire=3600)
    
    return {"suggestions": suggestions}

@router.delete("/session/{session_id}", response_model=ApiResponse)
async def clear_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """Limpiar historial de una sesión específica"""
    
    # Limpiar del cache de Redis
    cache_key = f"chat_session:{current_user.id}:{session_id}"
    await RedisCache.delete(cache_key)
    
    return ApiResponse(
        success=True,
        message="Sesión limpiada exitosamente"
    )
