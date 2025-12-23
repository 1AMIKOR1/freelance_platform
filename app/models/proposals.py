from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.projects import ProjectModel
    from app.models.freelancers import FreelancerModel


class ProposalModel(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    cover_message: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(default="pending")  # pending, accepted, rejected
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    project: Mapped["ProjectModel"] = relationship(back_populates="proposals")

    freelancer_id: Mapped[int] = mapped_column(ForeignKey("freelancers.id"), nullable=False)
    freelancer: Mapped["FreelancerModel"] = relationship(back_populates="proposals")