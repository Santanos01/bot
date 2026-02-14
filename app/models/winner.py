from datetime import datetime
from sqlalchemy import Integer, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Winner(Base):
    __tablename__ = "winners"
    __table_args__ = (
        Index("ix_winners_giveaway_id", "giveaway_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    picked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
