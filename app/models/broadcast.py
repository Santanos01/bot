from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Broadcast(Base):
    __tablename__ = "broadcasts"
    __table_args__ = (
        Index("ix_broadcasts_giveaway_id", "giveaway_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int] = mapped_column(ForeignKey("giveaways.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_fail: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
