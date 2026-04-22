from uuid import UUID
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.app.repositories.payment_repository import PaymentRepositoryInterface
from src.app.models.payment import Currency, PaymentStatus
from src.app.schemas.payment import PaymentResponse, PaymentDetailResponse


class PaymentService:
    """Сервис для работы с платежами"""

    def __init__(self, session: AsyncSession, repository: PaymentRepositoryInterface):
        self.session = session
        self.payment_repo = repository

    async def create_payment(
            self,
            idempotency_key: str,
            amount: Decimal,
            currency: Currency,
            description: str,
            webhook_url: str,
            metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResponse:
        """
        Создание платежа.
        """
        payment = await self.payment_repo.create_with_outbox(
            idempotency_key=idempotency_key,
            amount=amount,
            currency=currency,
            description=description,
            webhook_url=webhook_url,
            payment_metadata=metadata
        )

        await self.session.commit()

        return PaymentResponse(
            id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.payment_metadata,
            webhook_url=payment.webhook_url,
            processed_at=payment.processed_at,
            error_message=payment.error_message
        )

    async def get_payment(self, payment_id: UUID) -> Optional[PaymentDetailResponse]:
        """
        Получение детальной информации о платеже
        """
        payment = await self.payment_repo.get_by_id(payment_id)

        if not payment:
            return None

        return PaymentDetailResponse(
            id=payment.id,
            idempotency_key=payment.idempotency_key,
            status=payment.status,
            created_at=payment.created_at,
            updated_at=payment.updated_at,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.payment_metadata,
            webhook_url=payment.webhook_url,
            processed_at=payment.processed_at,
            error_message=payment.error_message,
            retry_count=payment.retry_count
        )

    async def update_payment_status(
            self,
            payment_id: UUID,
            status: PaymentStatus,
            error_message: Optional[str] = None
    ) -> Optional[PaymentResponse]:
        """
        Обновление статуса платежа (для consumer)
        """
        payment = await self.payment_repo.update_status(
            payment_id=payment_id,
            status=status,
            error_message=error_message
        )

        if payment:
            await self.session.commit()

            return PaymentResponse(
                id=payment.id,
                status=payment.status,
                created_at=payment.created_at,
                amount=payment.amount,
                currency=payment.currency,
                description=payment.description,
                metadata=payment.payment_metadata,
                webhook_url=payment.webhook_url,
                processed_at=payment.processed_at,
                error_message=payment.error_message
            )
        return None
