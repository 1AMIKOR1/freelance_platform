from typing import TYPE_CHECKING, List

from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.roles import RoleModel
    from app.models.freelancers import FreelancerModel
    from app.models.projects import ProjectModel
    from app.models.responces import ResponseModel


class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(300), nullable=False)

    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    role: Mapped["RoleModel"] = relationship(back_populates="users")

    freelancer_profile: Mapped["FreelancerModel"] = relationship(back_populates="user")
    projects: Mapped[List["ProjectModel"]] = relationship(back_populates="client")
    responses: Mapped[List["ResponseModel"]] = relationship(back_populates="freelancer")
