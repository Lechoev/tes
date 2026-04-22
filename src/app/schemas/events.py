from uuid import UUID
from decimal import Decimal
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel

from src.app.models.payment import Currency


class PaymentCreatedEvent(BaseModel):
    event_type: str = "payment.created"
    payment_id: UUID
    amount: Decimal
    currency: Currency
    webhook_url: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class PaymentProcessedEvent(BaseModel):
    event_type: str = "payment.processed"
    payment_id: UUID
    status: str
    error_message: Optional[str] = None
    processed_at: datetime
