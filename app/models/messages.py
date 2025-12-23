from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.users import UserModel


class MessageModel(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_read: Mapped[bool] = mapped_column(default=False)

    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    sender: Mapped["UserModel"] = relationship(foreign_keys=[sender_id])
    recipient: Mapped["UserModel"] = relationship(foreign_keys=[recipient_id])