from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram import Bot
from app.services.giveaways import finalize_giveaway, finalize_and_notify

_scheduler: Optional[AsyncIOScheduler] = None
_bot: Optional[Bot] = None


def set_scheduler(scheduler: AsyncIOScheduler) -> None:
    global _scheduler
    _scheduler = scheduler


def set_bot(bot: Bot) -> None:
    global _bot
    _bot = bot


def schedule_giveaway_end(giveaway_id: int, ends_at: datetime | None) -> None:
    if not ends_at or _scheduler is None:
        return
    if _bot is not None:
        _scheduler.add_job(
            finalize_and_notify,
            "date",
            run_date=ends_at,
            args=[_bot, giveaway_id],
            id=f"giveaway_{giveaway_id}",
            replace_existing=True,
        )
        return
    _scheduler.add_job(
        finalize_giveaway,
        "date",
        run_date=ends_at,
        args=[giveaway_id],
        id=f"giveaway_{giveaway_id}",
        replace_existing=True,
    )
