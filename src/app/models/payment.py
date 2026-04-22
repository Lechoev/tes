from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import (
    String, Numeric, DateTime, Enum as SQLEnum,
    JSON, Index, CheckConstraint, TIMESTAMP
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from src.app import conf


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Payment(conf.Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )
    currency: Mapped[Currency] = mapped_column(
        SQLEnum(Currency),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    payment_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True
    )
    status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
        index=True
    )
    webhook_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True
    )
    retry_count: Mapped[int] = mapped_column(default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        Index("ix_payments_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Payment(id={self.id}, status={self.status}, amount={self.amount} {self.currency})>"
