import asyncio

from src.app.brokers.rabbit import broker, payments_exchange, payments_dlq, payments_queue
from src.app.consumers.payment_consumer import router
from src.app.services.outbox_publisher import OutboxPublisher
from src.app.conf import db_manager, settings


async def main():
    db_manager.init(settings.database_url)

    broker.include_router(router)

    await broker.start()

    await broker.declare_exchange(payments_exchange)
    await broker.declare_queue(payments_queue)
    await broker.declare_queue(payments_dlq)

    publisher = OutboxPublisher(db_manager)
    publisher_task = asyncio.create_task(publisher.start())

    try:
        await asyncio.Future()
    finally:
        await publisher.stop()
        publisher_task.cancel()
        await broker.close()
        await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())
