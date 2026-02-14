import asyncio
import sys
import logging
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config.config import settings
from app.handlers import start, admin, callbacks, broadcast
from app.scheduler import set_scheduler, schedule_giveaway_end, set_bot
from app.services.giveaways import list_active_giveaways, mark_giveaway_finished_if_expired
from app.services.broadcast_jobs import run_broadcast_worker


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def _startup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=timezone.utc)
    scheduler.add_job(
        mark_giveaway_finished_if_expired,
        "interval",
        minutes=1,
        id="safety_expired",
        args=[bot],
    )
    set_scheduler(scheduler)
    set_bot(bot)

    giveaways = await list_active_giveaways()
    now = datetime.now(timezone.utc)
    for giveaway in giveaways:
        if giveaway.ends_at and giveaway.ends_at > now:
            schedule_giveaway_end(giveaway.id, giveaway.ends_at)
    scheduler.start()
    return scheduler


async def main() -> None:
    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(callbacks.router)
    dp.include_router(broadcast.router)

    await _startup_scheduler(bot)
    asyncio.create_task(run_broadcast_worker(bot))

    await dp.start_polling(bot)


if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
