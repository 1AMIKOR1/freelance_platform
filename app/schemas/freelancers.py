from pydantic import BaseModel, ConfigDict
from typing import Optional

class FreelancerBase(BaseModel):
    bio: Optional[str] = None
    hourly_rate: Optional[float] = None
    portfolio_url: Optional[str] = None

class FreelancerCreate(FreelancerBase):
    user_id: int

class FreelancerUpdate(FreelancerBase):
    pass

class Freelancer(FreelancerBase):
    id: int
    user_id: int
    
    model_config = ConfigDict(from_attributes=True)