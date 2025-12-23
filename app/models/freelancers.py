from typing import TYPE_CHECKING, List
from sqlalchemy import Text, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.users import UserModel
    from app.models.proposals import ProposalModel
    from app.models.reviews import ReviewModel
    from app.models.freelancer_skills import FreelancerSkillModel


class FreelancerModel(Base):
    __tablename__ = "freelancers"

    id: Mapped[int] = mapped_column(primary_key=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)
    hourly_rate: Mapped[float] = mapped_column(nullable=True)
    portfolio_url: Mapped[str] = mapped_column(String(255), nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    user: Mapped["UserModel"] = relationship(back_populates="freelancer_profile")

    proposals: Mapped[List["ProposalModel"]] = relationship(back_populates="freelancer")
    reviews: Mapped[List["ReviewModel"]] = relationship(back_populates="freelancer")
    skills_assoc: Mapped[List["FreelancerSkillModel"]] = relationship(back_populates="freelancer")