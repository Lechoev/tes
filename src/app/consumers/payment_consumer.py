import asyncio
import random

from faststream.rabbit import RabbitRouter

from src.app.brokers.rabbit import payments_queue
from src.app.schemas.events import PaymentCreatedEvent
from src.app.services.payment_service import PaymentService
from src.app.services.webhook_sender import WebhookSender
from src.app.models.payment import PaymentStatus
from src.app.repositories.payment_repository import PaymentRepository
from src.app.conf import settings, db_manager

router = RabbitRouter()


@router.subscriber(payments_queue)
async def process_payment(event: PaymentCreatedEvent):
    """
    Consumer для обработки платежей.
    Эмулирует платежный шлюз (2-5 сек, 90% успех, 10% ошибка)
    """
    delay = random.uniform(settings.PAYMENT_MIN_DELAY, settings.PAYMENT_MAX_DELAY)
    await asyncio.sleep(delay)

    is_success = random.random() < settings.PAYMENT_SUCCESS_RATE

    async with db_manager.session() as session:
        repository = PaymentRepository(session)
        service = PaymentService(session=session, repository=repository)

        if is_success:
            payment = await service.update_payment_status(
                payment_id=event.payment_id,
                status=PaymentStatus.SUCCEEDED
            )
        else:
            payment = await service.update_payment_status(
                payment_id=event.payment_id,
                status=PaymentStatus.FAILED,
                error_message="Payment gateway error"
            )

        if payment:
            webhook_sender = WebhookSender()
            await webhook_sender.send_webhook(
                webhook_url=event.webhook_url,
                payment_id=event.payment_id,
                status=payment.status,
                amount=event.amount,
                currency=event.currency,
                error_message=payment.error_message
            )
