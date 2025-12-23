from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="USD", pattern="^[A-Z]{3}$")
    status: str = Field(default="pending", pattern="^(pending|completed|failed)$")

class PaymentCreate(PaymentBase):
    proposal_id: int = Field(..., ge=1)

class PaymentUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    currency: Optional[str] = Field(None, pattern="^[A-Z]{3}$")
    status: Optional[str] = Field(None, pattern="^(pending|completed|failed)$")
    payment_date: Optional[datetime] = None

class Payment(PaymentBase):
    id: int
    proposal_id: int
    payment_date: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)