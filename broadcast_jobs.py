import asyncio
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, update, asc
from sqlalchemy.exc import IntegrityError
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter

from app.db.session import AsyncSessionLocal
from app.models.broadcast_job import BroadcastJob
from app.models.participant import Participant
from app.models.user import User
from app.services.sender import send_message_limited
from app.utils.telegram import contact_button_markup
from app.services.users import mark_user_cant_dm
logger = logging.getLogger(__name__)


async def create_broadcast_job(
    text: str,
    organizer: str | None,
    giveaway_id: int | None,
    is_global: bool,
) -> BroadcastJob | None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(BroadcastJob).where(
                BroadcastJob.status.in_(["PENDING", "RUNNING"]),
                BroadcastJob.text == text,
                BroadcastJob.giveaway_id == giveaway_id,
                BroadcastJob.is_global == is_global,
            )
        )
        if existing.scalar_one_or_none():
            return None

        job = BroadcastJob(
            giveaway_id=giveaway_id,
            text=text,
            organizer=organizer,
            is_global=is_global,
            last_participant_id=None,
            last_user_id=None,
            sent_ok=0,
            sent_fail=0,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(job)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return None
        await session.refresh(job)
        return job


async def fetch_next_job() -> BroadcastJob | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BroadcastJob).where(BroadcastJob.status == "PENDING").order_by(asc(BroadcastJob.id))
        )
        return result.scalars().first()


async def recover_stale_running_jobs(stale_after_minutes: int = 15) -> int:
    threshold = datetime.now(timezone.utc) - timedelta(minutes=stale_after_minutes)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            update(BroadcastJob)
            .where(BroadcastJob.status == "RUNNING", BroadcastJob.updated_at < threshold)
            .values(status="PENDING", updated_at=datetime.now(timezone.utc))
        )
        await session.commit()
        return int(result.rowcount or 0)


async def update_job(job_id: int, **fields) -> None:
    fields["updated_at"] = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        await session.execute(update(BroadcastJob).where(BroadcastJob.id == job_id).values(**fields))
        await session.commit()


async def _iter_targets(job: BroadcastJob):
    if job.is_global:
        async with AsyncSessionLocal() as session:
            query = select(User.user_id).where(User.can_dm == True)
            if job.last_user_id:
                query = query.where(User.user_id > job.last_user_id)
            query = query.order_by(User.user_id.asc())
            result = await session.execute(query)
            for (user_id,) in result.all():
                yield user_id
        return

    async with AsyncSessionLocal() as session:
        query = (
            select(Participant.id, Participant.user_id)
            .join(User, User.user_id == Participant.user_id)
            .where(
                Participant.giveaway_id == job.giveaway_id,
                Participant.can_dm == True,
                User.can_dm == True,
            )
        )
        if job.last_participant_id:
            query = query.where(Participant.id > job.last_participant_id)
        query = query.order_by(Participant.id.asc())
        result = await session.execute(query)
        for pid, user_id in result.all():
            yield pid, user_id


async def run_broadcast_worker(bot: Bot, throttle_delay: float = 0.12) -> None:
    while True:
        try:
            recovered = await recover_stale_running_jobs()
            if recovered:
                logger.warning("Recovered %s stale RUNNING broadcast job(s)", recovered)

            job = await fetch_next_job()
            if not job:
                await asyncio.sleep(1.0)
                continue

            await update_job(job.id, status="RUNNING")
            text = (
                "📣 <b>Сообщение от организатора:</b>\n"
                f"<b>{job.organizer or ''}</b>\n\n"
                f"{job.text}"
            )
            reply_markup = contact_button_markup(text)

            if job.is_global:
                async for user_id in _iter_targets(job):
                    try:
                        await asyncio.wait_for(
                            send_message_limited(bot, user_id, text, reply_markup=reply_markup, user_id=user_id),
                            timeout=30,
                        )
                        job.sent_ok += 1
                        job.last_user_id = user_id
                    except asyncio.TimeoutError:
                        logger.warning("Timeout sending message to user %s", user_id)
                        job.sent_fail += 1
                    except TelegramRetryAfter as e:
                        logger.warning("RetryAfter %s sec", e.retry_after)
                        await asyncio.sleep(float(e.retry_after))
                    except (TelegramForbiddenError, TelegramBadRequest):
                        job.sent_fail += 1
                        await mark_user_cant_dm(user_id)
                    except Exception:
                        job.sent_fail += 1
                    await update_job(
                        job.id,
                        sent_ok=job.sent_ok,
                        sent_fail=job.sent_fail,
                        last_user_id=job.last_user_id,
                    )
                    await asyncio.sleep(throttle_delay)
            else:
                async for pid, user_id in _iter_targets(job):
                    try:
                        await asyncio.wait_for(
                            send_message_limited(bot, user_id, text, reply_markup=reply_markup, user_id=user_id),
                            timeout=30,
                        )
                        job.sent_ok += 1
                        job.last_participant_id = pid
                    except asyncio.TimeoutError:
                        logger.warning("Timeout sending message to user %s", user_id)
                        job.sent_fail += 1
                    except TelegramRetryAfter as e:
                        logger.warning("RetryAfter %s sec", e.retry_after)
                        await asyncio.sleep(float(e.retry_after))
                    except (TelegramForbiddenError, TelegramBadRequest):
                        job.sent_fail += 1
                        await mark_user_cant_dm(user_id)
                        await _mark_participant_cant_dm(job.giveaway_id, user_id)
                    except Exception:
                        job.sent_fail += 1
                    await update_job(
                        job.id,
                        sent_ok=job.sent_ok,
                        sent_fail=job.sent_fail,
                        last_participant_id=job.last_participant_id,
                    )
                    await asyncio.sleep(throttle_delay)

            await update_job(job.id, status="DONE")
        except Exception:
            logger.exception("Broadcast worker loop failed; retrying in 2s")
            await asyncio.sleep(2.0)


async def _mark_participant_cant_dm(giveaway_id: int | None, user_id: int) -> None:
    if not giveaway_id:
        return
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Participant)
            .where(Participant.giveaway_id == giveaway_id, Participant.user_id == user_id)
            .values(can_dm=False)
        )
        await session.commit()
