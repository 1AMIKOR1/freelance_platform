from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.database import Base

class ProjectStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ProjectModel(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    budget = Column(Float)
    deadline = Column(DateTime)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.OPEN)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    client = relationship("UserModel", back_populates="projects")
    responses = relationship("ResponseModel", back_populates="project", cascade="all, delete-orphan")