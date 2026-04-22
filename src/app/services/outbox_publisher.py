import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from src.app import conf
from src.app.brokers.rabbit import broker, payments_exchange
from src.app.models.outbox import OutboxEvent, OutboxStatus


class OutboxPublisher:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.running = False

    async def start(self):
        self.running = True
        while self.running:
            try:
                await self.process_batch()
                await asyncio.sleep(conf.settings.OUTBOX_POLL_INTERVAL)
            except Exception as e:
                print(f"Publisher error: {e}")
                await asyncio.sleep(5)

    async def stop(self):
        self.running = False

    async def process_batch(self):
        async with self.db_manager.session() as session:
            stmt = (
                select(OutboxEvent)
                .where(OutboxEvent.status == OutboxStatus.PENDING)
                .order_by(OutboxEvent.created_at)
                .limit(conf.settings.OUTBOX_BATCH_SIZE)
                .with_for_update(skip_locked=True)
            )

            result = await session.execute(stmt)
            events = result.scalars().all()

            if not events:
                return

            for event in events:
                try:
                    await broker.publish(
                        message=event.payload,
                        exchange=payments_exchange,
                        routing_key="payment.created",
                        content_type="application/json"
                    )
                    event.status = OutboxStatus.PROCESSED
                    event.processed_at = datetime.now(timezone.utc)
                except Exception as e:
                    event.retry_count += 1
                    event.last_error = str(e)
                    if event.retry_count >= 3:
                        event.status = OutboxStatus.FAILED
            await session.commit()
