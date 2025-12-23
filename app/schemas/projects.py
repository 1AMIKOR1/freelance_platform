from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.projects import ProjectStatus

class ProjectBase(BaseModel):
    title: str
    description: str
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    status: Optional[ProjectStatus] = ProjectStatus.OPEN

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    deadline: Optional[datetime] = None
    status: Optional[ProjectStatus] = None

class Project(ProjectBase):
    id: int
    client_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True