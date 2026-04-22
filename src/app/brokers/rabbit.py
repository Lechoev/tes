from faststream.rabbit import RabbitBroker, RabbitQueue, RabbitExchange, ExchangeType

from src.app.conf import settings

broker = RabbitBroker(settings.RABBITMQ_URL)

payments_exchange = RabbitExchange(
    name=settings.PAYMENTS_EXCHANGE,
    type=ExchangeType.DIRECT,
    durable=True
)

payments_queue = RabbitQueue(
    name=settings.PAYMENTS_QUEUE,
    durable=True,
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": settings.PAYMENTS_DLQ,
        "x-message-ttl": 30000,
        "x-max-retries": 3
    }
)

payments_dlq = RabbitQueue(
    name=settings.PAYMENTS_DLQ,
    durable=True
)
