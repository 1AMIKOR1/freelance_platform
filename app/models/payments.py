from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import Numeric, ForeignKey, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

if TYPE_CHECKING:
    from app.models.proposals import ProposalModel


class PaymentModel(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, completed, failed
    payment_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    proposal_id: Mapped[int] = mapped_column(ForeignKey("proposals.id"), nullable=False)
    proposal: Mapped["ProposalModel"] = relationship(back_populates="payment")