"""
Rutas para pagos con Stripe
"""

import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from core.config import settings
from models import User, Payment as PaymentModel
from schemas import PaymentCreate, Payment as PaymentSchema, ApiResponse
from api.routes.auth import get_current_user

# Configurar Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()

@router.post("/create-session")
async def create_payment_session(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Crear sesión de pago con Stripe"""
    
    try:
        # Crear sesión de Stripe Checkout
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': payment_data.currency.lower(),
                    'product_data': {
                        'name': payment_data.description or 'Servicio Tramites AI',
                    },
                    'unit_amount': int(payment_data.amount * 100),  # Stripe usa centavos
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{settings.ALLOWED_ORIGINS[0]}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.ALLOWED_ORIGINS[0]}/payment/cancel",
            customer_email=current_user.email,
            metadata={
                'user_id': str(current_user.id),
                'description': payment_data.description or ''
            }
        )
        
        # Guardar información del pago en base de datos
        payment = PaymentModel(
            user_id=current_user.id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            stripe_session_id=session.id,
            status="pending"
        )
        
        db.add(payment)
        await db.commit()
        await db.refresh(payment)
        
        return {
            "session_id": session.id,
            "session_url": session.url,
            "payment_id": str(payment.id)
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de Stripe: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creando sesión de pago: {str(e)}"
        )

@router.get("/session/{session_id}")
async def get_payment_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener información de sesión de pago"""
    
    try:
        # Obtener sesión de Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Verificar que la sesión pertenece al usuario
        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.stripe_session_id == session_id,
                PaymentModel.user_id == current_user.id
            )
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sesión de pago no encontrada"
            )
        
        return {
            "session": {
                "id": session.id,
                "status": session.payment_status,
                "amount_total": session.amount_total,
                "currency": session.currency,
                "customer_email": session.customer_email
            },
            "payment": payment
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error de Stripe: {str(e)}"
        )

@router.get("/my-payments")
async def get_my_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtener historial de pagos del usuario"""
    
    result = await db.execute(
        select(PaymentModel).where(
            PaymentModel.user_id == current_user.id
        ).order_by(PaymentModel.created_at.desc())
    )
    payments = result.scalars().all()
    
    return {"payments": payments}

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Webhook para eventos de Stripe"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma inválida")
    
    # Procesar eventos
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_successful_payment(session, db)
    
    elif event['type'] == 'checkout.session.expired':
        session = event['data']['object']
        await handle_expired_payment(session, db)
    
    return {"status": "success"}

async def handle_successful_payment(session, db: AsyncSession):
    """Manejar pago exitoso"""
    
    # Actualizar estado del pago
    result = await db.execute(
        select(PaymentModel).where(
            PaymentModel.stripe_session_id == session['id']
        )
    )
    payment = result.scalar_one_or_none()
    
    if payment:
        payment.status = "completed"
        payment.stripe_payment_id = session.get('payment_intent')
        payment.stripe_customer_id = session.get('customer')
        
        # Si es un pago de premium, actualizar usuario
        if "premium" in (payment.description or "").lower():
            result = await db.execute(
                select(User).where(User.id == payment.user_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.is_premium = True
        
        await db.commit()

async def handle_expired_payment(session, db: AsyncSession):
    """Manejar pago expirado"""
    
    result = await db.execute(
        select(PaymentModel).where(
            PaymentModel.stripe_session_id == session['id']
        )
    )
    payment = result.scalar_one_or_none()
    
    if payment:
        payment.status = "expired"
        await db.commit()

@router.get("/plans")
async def get_payment_plans():
    """Obtener planes de pago disponibles"""
    
    plans = [
        {
            "id": "basic",
            "name": "Plan Básico",
            "price": 0,
            "currency": "PEN",
            "description": "Acceso básico a consultas de IA",
            "features": [
                "10 consultas por día",
                "Búsqueda de procedimientos",
                "Información básica"
            ]
        },
        {
            "id": "premium",
            "name": "Plan Premium",
            "price": 29.90,
            "currency": "PEN",
            "description": "Acceso completo a todas las funcionalidades",
            "features": [
                "Consultas ilimitadas",
                "Generación de documentos",
                "Soporte prioritario",
                "Alertas personalizadas",
                "Historial completo"
            ]
        }
    ]
    
    return {"plans": plans}
