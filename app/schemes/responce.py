from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ResponseBase(BaseModel):
    message: str
    proposed_price: Optional[float] = None

class ResponseCreate(ResponseBase):
    project_id: int

class Response(ResponseBase):
    id: int
    freelancer_id: int
    project_id: int
    is_selected: bool
    created_at: datetime
    
    class Config:
        from_attributes = True