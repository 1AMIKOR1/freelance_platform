from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

class MessageCreate(MessageBase):
    recipient_id: int = Field(..., ge=1)

class MessageUpdate(BaseModel):
    is_read: Optional[bool] = None

class Message(MessageBase):
    id: int
    sender_id: int
    recipient_id: int
    timestamp: datetime
    is_read: bool
    
    model_config = ConfigDict(from_attributes=True)