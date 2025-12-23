from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.freelancers import FreelancerModel
    from app.models.skills import SkillModel


class FreelancerSkillModel(Base):
    __tablename__ = "freelancer_skills"

    freelancer_id: Mapped[int] = mapped_column(ForeignKey("freelancers.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)

    freelancer: Mapped["FreelancerModel"] = relationship(back_populates="skills_assoc")
    skill: Mapped["SkillModel"] = relationship(back_populates="freelancers_assoc")