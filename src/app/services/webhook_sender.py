import asyncio
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

import aiohttp

from src.app.models.payment import PaymentStatus
from src.app.schemas.payment import WebhookPayload
from src.app.conf import settings


class WebhookSender:
    """Отправка webhook уведомлений с ретраями"""

    async def send_webhook(
            self,
            webhook_url: str,
            payment_id: UUID,
            status: PaymentStatus,
            amount: Decimal,
            currency: str,
            error_message: Optional[str] = None
    ):
        """Отправка webhook с экспоненциальными ретраями"""

        payload = WebhookPayload(
            payment_id=payment_id,
            status=status,
            amount=amount,
            currency=currency,
            processed_at=datetime.now(timezone.utc),
            error_message=error_message
        )

        for attempt in range(settings.WEBHOOK_MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                            webhook_url,
                            json=payload.model_dump(),
                            timeout=aiohttp.ClientTimeout(total=settings.WEBHOOK_TIMEOUT)
                    ) as response:
                        if response.status in (200, 201, 202):
                            return
            except Exception as e:
                pass

            if attempt < settings.WEBHOOK_MAX_RETRIES - 1:
                delay = settings.WEBHOOK_RETRY_DELAYS[attempt]
                await asyncio.sleep(delay)
