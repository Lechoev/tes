from abc import ABC, abstractmethod
from uuid import UUID
from decimal import Decimal
from typing import Optional, Dict, Any, Sequence
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from src.app.models.payment import Payment, PaymentStatus, Currency
from src.app.models.outbox import OutboxEvent


class PaymentRepositoryInterface(ABC):
    @abstractmethod
    async def create_with_outbox(
            self,
            idempotency_key: str,
            amount: Decimal,
            currency: Currency,
            description: str,
            webhook_url: str,
            payment_metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """Создание платежа и outbox события в одной транзакции"""
        ...

    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        """Получение платежа по ID"""
        ...

    @abstractmethod
    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        """Получение платежа по ключу идемпотентности"""
        ...

    @abstractmethod
    async def update_status(
            self,
            payment_id: UUID,
            status: PaymentStatus,
            error_message: Optional[str] = None
    ) -> Optional[Payment]:
        """Обновление статуса платежа"""
        ...

    @abstractmethod
    async def get_pending_payments(
            self,
            limit: int = 100,
            offset: int = 0
    ) -> Sequence[Payment]:
        """Получение списка pending платежей"""
        ...


class PaymentRepository(PaymentRepositoryInterface):
    """Репозиторий для работы с платежами"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_with_outbox(
            self,
            idempotency_key: str,
            amount: Decimal,
            currency: Currency,
            description: str,
            webhook_url: str,
            payment_metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """Создание платежа и outbox события в одной транзакции"""
        existing = await self.get_by_idempotency_key(idempotency_key)
        if existing:
            return existing

        payment = Payment(
            idempotency_key=idempotency_key,
            amount=amount,
            currency=currency,
            description=description,
            webhook_url=str(webhook_url),
            payment_metadata=payment_metadata or {},
            status=PaymentStatus.PENDING
        )
        self.session.add(payment)

        await self.session.flush()

        outbox_event = OutboxEvent(
            aggregate_id=payment.id,
            event_type="payment.created",
            payload={
                "payment_id": str(payment.id),
                "amount": str(amount),
                "currency": currency.value,
                "webhook_url": str(webhook_url),
                "metadata": payment_metadata,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self.session.add(outbox_event)

        return payment

    async def get_by_id(self, payment_id: UUID) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_idempotency_key(self, key: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def update_status(
            self,
            payment_id: UUID,
            status: PaymentStatus,
            error_message: Optional[str] = None
    ) -> Optional[Payment]:
        now = datetime.now(timezone.utc)  # ✅ Вычисляем один раз
        now_naive = now.replace(tzinfo=None)

        stmt = (
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=status,
                error_message=error_message,
                processed_at=now_naive if status != PaymentStatus.PENDING else None,
                updated_at=now_naive
            )
            .returning(Payment)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    async def get_pending_payments(
            self,
            limit: int = 100,
            offset: int = 0
    ) -> Sequence[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.created_at)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
