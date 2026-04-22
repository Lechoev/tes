from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_USER: str = "postgres"
    DB_NAME: str = "payments_db"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"

    # API
    API_KEY: str = "secret-api-key"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"
    PAYMENTS_QUEUE: str = "payments.new"
    PAYMENTS_DLQ: str = "payments.new.dlq"
    PAYMENTS_EXCHANGE: str = "payments.exchange"
    PAYMENTS_ROUTING_KEY: str = "payment.created"

    # Outbox Publisher
    OUTBOX_POLL_INTERVAL: float = 1.0
    OUTBOX_BATCH_SIZE: int = 100

    # Payment processing
    PAYMENT_MIN_DELAY: float = 2.0
    PAYMENT_MAX_DELAY: float = 5.0
    PAYMENT_SUCCESS_RATE: float = 0.9

    # Webhook
    WEBHOOK_TIMEOUT: float = 10.0
    WEBHOOK_MAX_RETRIES: int = 3
    WEBHOOK_RETRY_DELAYS: List[int] = [1, 5, 25]

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
