import uuid

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import String, JSON, Integer, Index, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.app import conf


class OutboxStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class OutboxEvent(conf.Base):
    __tablename__ = "outbox"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    aggregate_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )
    payload: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False
    )
    status: Mapped[OutboxStatus] = mapped_column(
        String(20),
        nullable=False,
        default=OutboxStatus.PENDING,
        index=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    __table_args__ = (
        Index("ix_outbox_pending", "status", "created_at"),
        Index("ix_outbox_aggregate_type", "aggregate_id", "event_type"),
    )

    def __repr__(self) -> str:
        return f"<OutboxEvent(id={self.id}, type={self.event_type}, status={self.status})>"
