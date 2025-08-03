"""
Esquemas Pydantic para validación y serialización
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

# Esquemas de Usuario
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    document_type: Optional[str] = "dni"
    document_number: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    document_type: Optional[str] = None
    document_number: Optional[str] = None

class User(UserBase):
    id: UUID
    is_active: bool
    is_verified: bool
    is_premium: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Esquemas de Entidad
class EntityBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    sector: Optional[str] = None

class EntityCreate(EntityBase):
    parent_entity_id: Optional[UUID] = None

class Entity(EntityBase):
    id: UUID
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Esquemas de Procedimiento
class ProcedureBase(BaseModel):
    name: str
    description: Optional[str] = None
    tupa_code: Optional[str] = None
    requirements: Optional[List[str]] = None
    cost: Optional[float] = None
    currency: str = "PEN"
    processing_time: Optional[str] = None
    legal_basis: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    is_free: bool = False
    is_online: bool = False
    difficulty_level: str = "medium"
    keywords: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class ProcedureCreate(ProcedureBase):
    entity_id: UUID

class ProcedureUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[List[str]] = None
    cost: Optional[float] = None
    processing_time: Optional[str] = None
    is_free: Optional[bool] = None
    is_online: Optional[bool] = None
    difficulty_level: Optional[str] = None

class Procedure(ProcedureBase):
    id: UUID
    entity: Entity
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProcedureSearch(BaseModel):
    query: str
    entity_id: Optional[UUID] = None
    category: Optional[str] = None
    is_free: Optional[bool] = None
    is_online: Optional[bool] = None
    limit: int = 10
    offset: int = 0

# Esquemas de Consulta
class QueryBase(BaseModel):
    original_query: str
    intent: Optional[str] = None

class QueryCreate(QueryBase):
    procedure_id: Optional[UUID] = None
    session_id: Optional[str] = None

class Query(QueryBase):
    id: UUID
    user_id: UUID
    ai_response: Optional[str] = None
    confidence_score: Optional[float] = None
    response_time: Optional[float] = None
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    was_helpful: Optional[bool] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class QueryFeedback(BaseModel):
    query_id: UUID
    rating: int
    feedback: Optional[str] = None
    was_helpful: bool
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('El rating debe estar entre 1 y 5')
        return v

# Esquemas de Chat
class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    procedures: Optional[List[Procedure]] = None
    confidence: float
    response_time: float
    suggestions: Optional[List[str]] = None

# Esquemas de Documento
class DocumentBase(BaseModel):
    name: str
    document_type: str

class DocumentCreate(DocumentBase):
    template_data: Dict[str, Any]

class Document(DocumentBase):
    id: UUID
    user_id: UUID
    file_path: str
    file_size: int
    mime_type: str
    status: str
    download_count: int
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquemas de Pago
class PaymentBase(BaseModel):
    amount: float
    currency: str = "PEN"
    description: Optional[str] = None

class PaymentCreate(PaymentBase):
    payment_method: str = "card"

class Payment(PaymentBase):
    id: UUID
    user_id: UUID
    stripe_payment_id: Optional[str] = None
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class PaymentWebhook(BaseModel):
    type: str
    data: Dict[str, Any]

# Esquemas de respuesta
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# Esquemas de administración
class AdminStats(BaseModel):
    total_users: int
    total_procedures: int
    total_queries: int
    total_documents: int
    daily_queries: int
    monthly_revenue: float

class HealthCheck(BaseModel):
    status: str
    database: str
    redis: str
    timestamp: datetime
