from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Text, ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.users import UserModel
    from app.models.freelancers import FreelancerModel


class ReviewModel(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–5
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)  # обычно клиент
    freelancer_id: Mapped[int] = mapped_column(ForeignKey("freelancers.id"), nullable=False)

    reviewer: Mapped["UserModel"] = relationship(foreign_keys=[reviewer_id])
    freelancer: Mapped["FreelancerModel"] = relationship(back_populates="reviews")