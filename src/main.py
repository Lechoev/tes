from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
import asyncio

from src.app import conf
from src.app.api.v1 import payments
from src.app.brokers.rabbit import broker
from src.app.services.outbox_publisher import OutboxPublisher


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    conf.db_manager.init(conf.settings.database_url)

    await broker.start()

    publisher = OutboxPublisher(conf.db_manager)
    publisher_task = asyncio.create_task(publisher.start())

    yield

    await publisher.stop()
    publisher_task.cancel()
    await broker.close()
    await conf.db_manager.close()


app = FastAPI(title="Payment Processing Service", lifespan=lifespan)

app.include_router(payments.router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}