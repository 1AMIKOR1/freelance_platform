from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class ProposalBase(BaseModel):
    cover_message: str = Field(..., min_length=10, max_length=2000)
    proposed_price: float = Field(..., gt=0)
    status: str = Field(default="pending", pattern="^(pending|accepted|rejected)$")

class ProposalCreate(ProposalBase):
    project_id: int = Field(..., ge=1)
    freelancer_id: int = Field(..., ge=1)

class ProposalUpdate(BaseModel):
    cover_message: Optional[str] = Field(None, min_length=10, max_length=2000)
    proposed_price: Optional[float] = Field(None, gt=0)
    status: Optional[str] = Field(None, pattern="^(pending|accepted|rejected)$")

class Proposal(ProposalBase):
    id: int
    project_id: int
    freelancer_id: int
    submitted_at: datetime
    
    model_config = ConfigDict(from_attributes=True)