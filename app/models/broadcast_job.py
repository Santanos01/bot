from datetime import datetime
from sqlalchemy import Integer, Text, DateTime, String, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class BroadcastJob(Base):
    __tablename__ = "broadcast_jobs"
    __table_args__ = (
        Index("ix_broadcast_jobs_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    giveaway_id: Mapped[int | None] = mapped_column(ForeignKey("giveaways.id", ondelete="SET NULL"))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    organizer: Mapped[str | None] = mapped_column(String(128))
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    last_participant_id: Mapped[int | None] = mapped_column(Integer)
    last_user_id: Mapped[int | None] = mapped_column(Integer)
    sent_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sent_fail: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
