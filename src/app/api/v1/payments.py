from fastapi import APIRouter, Depends, HTTPException, status, Header
from uuid import UUID

from src.app.services.payment_service import PaymentService
from src.app.schemas.payment import PaymentCreateRequest, PaymentResponse, PaymentDetailResponse
from src.app.api.dependencies import get_payment_service
from src.app.conf import settings

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """Проверка API ключа"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key


@router.post(
    "/",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=PaymentResponse
)
async def create_payment(
        payment_data: PaymentCreateRequest,
        idempotency_key: str = Header(..., alias="Idempotency-Key"),
        api_key: str = Depends(verify_api_key),
        payment_service: PaymentService = Depends(get_payment_service)
):
    try:
        payment = await payment_service.create_payment(
            idempotency_key=idempotency_key,
            amount=payment_data.amount,
            currency=payment_data.currency,
            description=payment_data.description,
            webhook_url=str(payment_data.webhook_url),
            metadata=payment_data.metadata
        )
        return payment
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(
        payment_id: UUID,
        api_key: str = Depends(verify_api_key),
        payment_service: PaymentService = Depends(get_payment_service)
):
    """Получение детальной информации о платеже"""
    payment = await payment_service.get_payment(payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    return payment
