from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional

class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)

class ReviewCreate(ReviewBase):
    project_id: int = Field(..., ge=1)
    reviewer_id: int = Field(..., ge=1)
    freelancer_id: int = Field(..., ge=1)

class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)

class Review(ReviewBase):
    id: int
    project_id: int
    reviewer_id: int
    freelancer_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)