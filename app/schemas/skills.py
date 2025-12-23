from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class SkillBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)

class Skill(SkillBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)