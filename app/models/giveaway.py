from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Giveaway(Base):
    __tablename__ = "giveaways"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    channel_username: Mapped[str] = mapped_column(String(128), nullable=False)
    winner_message: Mapped[str | None] = mapped_column(Text)
    winners_mode: Mapped[str] = mapped_column(String(16), nullable=False)  # COUNT or ALL
    winners_count: Mapped[int | None] = mapped_column(Integer)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="ACTIVE")
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
