"""
Rutas para generación y gestión de documentos
"""

import os
import uuid
import aiofiles
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any

from core.database import get_db
from core.config import settings
from models import User, Document as DocumentModel
from schemas import DocumentCreate, Document as DocumentSchema, ApiResponse
from api.routes.auth import get_current_user
from services.document_service import DocumentService

router = APIRouter()

@router.post("/generate", response_model=DocumentSchema)
async def generate_document(
    document_data: DocumentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generar un documento basado en plantilla"""
    
    try:
        document_service = DocumentService()
        
        # Generar documento
        file_info = await document_service.generate_document(
            template_type=document_data.document_type,
            data=document_data.template_data,
            user_id=str(current_user.id)
        )
        
        # Guardar información en base de datos
        document = DocumentModel(
            user_id=current_user.id,
            name=document_data.name,
            document_type=document_data.document_type,
            file_path=file_info["file_path"],
            file_size=file_info["file_size"],
            mime_type=file_info["mime_type"],
            expires_at=datetime.utcnow() + timedelta(days=30)  # 30 días de vigencia
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generando documento: {str(e)}"
        )

@router.get("/templates")
async def get_document_templates():
    """Obtener lista de plantillas disponibles"""
    
    templates = [
        {
            "id": "solicitud_dni",
            "name": "Solicitud de DNI",
            "description": "Formato para solicitar DNI por primera vez o renovación",
            "category": "identidad",
            "fields": ["nombres", "apellidos", "fecha_nacimiento", "lugar_nacimiento", "direccion"]
        },
        {
            "id": "solicitud_pasaporte", 
            "name": "Solicitud de Pasaporte",
            "description": "Formato para solicitar pasaporte peruano",
            "category": "identidad",
            "fields": ["nombres", "apellidos", "dni", "telefono", "email", "motivo_viaje"]
        },
        {
            "id": "declaracion_jurada",
            "name": "Declaración Jurada",
            "description": "Formato de declaración jurada genérica",
            "category": "legal",
            "fields": ["nombres", "apellidos", "dni", "declaracion", "lugar", "fecha"]
        },
        {
            "id": "poder_simple",
            "name": "Poder Simple",
            "description": "Formato de poder para trámites específicos",
            "category": "legal", 
            "fields": ["poderdante", "dni_poderdante", "apoderado", "dni_apoderado", "facultades"]
        },
        {
            "id": "solicitud_empresa",
            "name": "Solicitud de Constitución de Empresa",
            "description": "Formato para constituir empresa en registros públicos",
            "category": "empresarial",
            "fields": ["razon_social", "tipo_empresa", "capital", "socios", "actividad_economica"]
        }
    ]
    
    return {"templates": templates}

@router.get("/my-documents")
async def get_my_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener documentos del usuario actual"""
    
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.user_id == current_user.id
        ).order_by(DocumentModel.created_at.desc())
    )
    documents = result.scalars().all()
    
    return {"documents": documents}

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Descargar un documento específico"""
    
    # Verificar que el documento pertenece al usuario
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Verificar que el archivo existe
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en el servidor"
        )
    
    # Verificar que no ha expirado
    if document.expires_at and document.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="El documento ha expirado"
        )
    
    # Incrementar contador de descargas
    document.download_count += 1
    await db.commit()
    
    return FileResponse(
        path=document.file_path,
        filename=document.name,
        media_type=document.mime_type
    )

@router.delete("/{document_id}", response_model=ApiResponse)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Eliminar un documento"""
    
    # Verificar que el documento pertenece al usuario
    result = await db.execute(
        select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento no encontrado"
        )
    
    # Eliminar archivo físico
    if os.path.exists(document.file_path):
        os.remove(document.file_path)
    
    # Eliminar registro de base de datos
    await db.delete(document)
    await db.commit()
    
    return ApiResponse(
        success=True,
        message="Documento eliminado exitosamente"
    )

@router.post("/upload", response_model=DocumentSchema)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = "upload",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Subir un documento del usuario"""
    
    # Validar tamaño del archivo
    if file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo es demasiado grande"
        )
    
    # Validar tipo de archivo
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "application/msword", 
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no permitido"
        )
    
    try:
        # Crear directorio de usuario si no existe
        user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)
        
        # Generar nombre único para el archivo
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(user_dir, unique_filename)
        
        # Guardar archivo
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Guardar información en base de datos
        document = DocumentModel(
            user_id=current_user.id,
            name=file.filename,
            document_type=document_type,
            file_path=file_path,
            file_size=len(content),
            mime_type=file.content_type,
            status="uploaded"
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error subiendo archivo: {str(e)}"
        )
