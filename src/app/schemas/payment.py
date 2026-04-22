from uuid import UUID
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class Currency(str, Enum):
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: Currency
    description: str = Field(..., min_length=1, max_length=500)
    metadata: Optional[Dict[str, Any]] = None
    webhook_url: HttpUrl


class PaymentResponse(BaseModel):
    id: UUID
    status: PaymentStatus
    created_at: datetime
    amount: Decimal
    currency: Currency
    description: str
    metadata: Optional[Dict[str, Any]] = None
    webhook_url: str
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class PaymentDetailResponse(PaymentResponse):
    idempotency_key: str
    updated_at: datetime
    retry_count: int

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    payment_id: UUID
    status: PaymentStatus
    amount: Decimal
    currency: Currency
    processed_at: datetime
    error_message: Optional[str] = None
