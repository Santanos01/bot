import random
import asyncio
from datetime import datetime, timezone
from typing import Sequence

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select, update, func, delete, distinct
from sqlalchemy.exc import IntegrityError

from app.db.session import AsyncSessionLocal
from app.models.giveaway import Giveaway
from app.models.participant import Participant
from app.models.winner import Winner
from app.models.broadcast import Broadcast
from app.utils.telegram import contact_button_markup
from app.services.sender import send_message_limited
from app.services.users import mark_user_cant_dm


async def check_subscription(bot: Bot, channel_username: str, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
    except TelegramBadRequest:
        return False
    return member.status in {"member", "administrator", "creator"}


async def get_giveaway(giveaway_id: int) -> Giveaway | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
        return result.scalar_one_or_none()


async def list_active_giveaways() -> Sequence[Giveaway]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Giveaway).where(Giveaway.status == "ACTIVE"))
        return result.scalars().all()


async def list_all_giveaways() -> Sequence[Giveaway]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Giveaway).order_by(Giveaway.id.desc()))
        return result.scalars().all()


async def global_stats() -> dict:
    async with AsyncSessionLocal() as session:
        total_giveaways = await session.execute(select(func.count()).select_from(Giveaway))
        active_giveaways = await session.execute(
            select(func.count()).select_from(Giveaway).where(Giveaway.status == "ACTIVE")
        )
        finished_giveaways = await session.execute(
            select(func.count()).select_from(Giveaway).where(Giveaway.status == "FINISHED")
        )
        total_participants = await session.execute(
            select(func.count(distinct(Participant.user_id))).select_from(Participant)
        )
        can_dm_users = await session.execute(
            select(func.count(distinct(Participant.user_id))).select_from(Participant).where(Participant.can_dm == True)
        )
        total_winners = await session.execute(select(func.count()).select_from(Winner))
        total_broadcasts = await session.execute(select(func.count()).select_from(Broadcast))

        return {
            "giveaways_total": int(total_giveaways.scalar_one()),
            "giveaways_active": int(active_giveaways.scalar_one()),
            "giveaways_finished": int(finished_giveaways.scalar_one()),
            "participants_total": int(total_participants.scalar_one()),
            "participants_can_dm": int(can_dm_users.scalar_one()),
            "winners_total": int(total_winners.scalar_one()),
            "broadcasts_total": int(total_broadcasts.scalar_one()),
        }


async def add_participant(giveaway_id: int, user_id: int, username: str | None) -> bool:
    async with AsyncSessionLocal() as session:
        ticket_number = random.randint(1000, 9999)
        participant = Participant(
            giveaway_id=giveaway_id,
            user_id=user_id,
            username=username,
            ticket_number=ticket_number,
            joined_at=datetime.now(timezone.utc),
            can_dm=True,
        )
        session.add(participant)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return False
        return True


async def get_participant(giveaway_id: int, user_id: int) -> Participant | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Participant).where(Participant.giveaway_id == giveaway_id, Participant.user_id == user_id)
        )
        return result.scalar_one_or_none()


async def participants_count(giveaway_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(Participant).where(Participant.giveaway_id == giveaway_id)
        )
        return int(result.scalar_one())


async def winners_count(giveaway_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(Winner).where(Winner.giveaway_id == giveaway_id)
        )
        return int(result.scalar_one())


async def broadcasts_count(giveaway_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(Broadcast).where(Broadcast.giveaway_id == giveaway_id)
        )
        return int(result.scalar_one())


async def list_participants(giveaway_id: int) -> Sequence[Participant]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Participant).where(Participant.giveaway_id == giveaway_id))
        return result.scalars().all()


def _pick_winners_ids(participants: Sequence[Participant], winners_mode: str, winners_count: int | None) -> list[int]:
    user_ids = [p.user_id for p in participants]
    if not user_ids:
        return []
    if winners_mode == "ALL":
        return user_ids
    if winners_count is None:
        return []
    k = min(winners_count, len(user_ids))
    return random.sample(user_ids, k=k)


async def pick_winners(giveaway: Giveaway) -> list[int]:
    participants = await list_participants(giveaway.id)
    return _pick_winners_ids(participants, giveaway.winners_mode, giveaway.winners_count)


async def finalize_giveaway(giveaway_id: int) -> list[int]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Giveaway).where(Giveaway.id == giveaway_id))
        giveaway = result.scalar_one_or_none()
        if not giveaway:
            return []
        if giveaway.status == "FINISHED":
            result = await session.execute(select(Winner.user_id).where(Winner.giveaway_id == giveaway_id))
            return list(result.scalars().all())

        result = await session.execute(select(Participant).where(Participant.giveaway_id == giveaway_id))
        participants = result.scalars().all()

        winners_ids = _pick_winners_ids(participants, giveaway.winners_mode, giveaway.winners_count)
        now = datetime.now(timezone.utc)
        for user_id in winners_ids:
            session.add(Winner(giveaway_id=giveaway_id, user_id=user_id, picked_at=now))

        giveaway.status = "FINISHED"
        await session.commit()
        return winners_ids


async def finalize_and_notify(bot: Bot, giveaway_id: int) -> tuple[list[int], int, int]:
    winners_ids = await finalize_giveaway(giveaway_id)
    if not winners_ids:
        return winners_ids, 0, 0

    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        return winners_ids, 0, 0

    base_text = giveaway.winner_message or "Поздравляем! Вы победитель розыгрыша."
    ok = 0
    fail = 0
    for user_id in winners_ids:
        participant = await get_participant(giveaway_id, user_id)
        ticket = participant.ticket_number if participant else "—"
        message_text = (
            "🏆 <b>Поздравляем! Вы выиграли!</b>\n"
            f"🎫 <b>Номер вашего билета:</b> #{ticket}\n\n"
            f"{base_text}"
        )
        reply_markup = contact_button_markup(message_text)
        try:
            await send_message_limited(bot, user_id, message_text, reply_markup=reply_markup, user_id=user_id)
            ok += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after))
            try:
                await send_message_limited(bot, user_id, message_text, reply_markup=reply_markup, user_id=user_id)
                ok += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                fail += 1
                await _mark_cant_dm_by_user(giveaway_id, user_id)
        except (TelegramForbiddenError, TelegramBadRequest):
            fail += 1
            await _mark_cant_dm_by_user(giveaway_id, user_id)
            await mark_user_cant_dm(user_id)
        except Exception:
            fail += 1
        await asyncio.sleep(0.12)
    return winners_ids, ok, fail


async def mark_giveaway_finished_if_expired(bot: Bot) -> list[int]:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Giveaway).where(Giveaway.status == "ACTIVE", Giveaway.ends_at != None, Giveaway.ends_at <= now)
        )
        giveaways = result.scalars().all()
    finished_ids: list[int] = []
    for giveaway in giveaways:
        winners, _, _ = await finalize_and_notify(bot, giveaway.id)
        if winners is not None:
            finished_ids.append(giveaway.id)
    return finished_ids


async def create_giveaway(
    title: str,
    description: str | None,
    channel_username: str,
    winner_message: str | None,
    winners_mode: str,
    winners_count: int | None,
    ends_at: datetime | None,
    created_by: int,
) -> Giveaway:
    async with AsyncSessionLocal() as session:
        giveaway = Giveaway(
            title=title,
            description=description,
            channel_username=channel_username,
            winner_message=winner_message,
            winners_mode=winners_mode,
            winners_count=winners_count,
            ends_at=ends_at,
            status="ACTIVE",
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
        )
        session.add(giveaway)
        await session.commit()
        await session.refresh(giveaway)
        return giveaway


async def set_giveaway_status(giveaway_id: int, status: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(update(Giveaway).where(Giveaway.id == giveaway_id).values(status=status))
        await session.commit()


async def update_giveaway_fields(giveaway_id: int, **fields) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(update(Giveaway).where(Giveaway.id == giveaway_id).values(**fields))
        await session.commit()


async def delete_giveaway(giveaway_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Giveaway).where(Giveaway.id == giveaway_id))
        await session.commit()


async def _mark_cant_dm_by_user(giveaway_id: int, user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Participant)
            .where(Participant.giveaway_id == giveaway_id, Participant.user_id == user_id)
            .values(can_dm=False)
        )
        await session.commit()
