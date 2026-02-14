import asyncio
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramRetryAfter
from sqlalchemy import select, update, distinct

from app.db.session import AsyncSessionLocal
from app.models.broadcast import Broadcast
from app.models.participant import Participant


async def broadcast_to_participants(
    bot: Bot, giveaway_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> tuple[int, int]:
    ok = 0
    fail = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Participant).where(Participant.giveaway_id == giveaway_id, Participant.can_dm == True)
        )
        participants = result.scalars().all()

    for participant in participants:
        try:
            await bot.send_message(chat_id=participant.user_id, text=text, reply_markup=reply_markup)
            ok += 1
            await asyncio.sleep(0.12)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after))
            try:
                await bot.send_message(chat_id=participant.user_id, text=text, reply_markup=reply_markup)
                ok += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                fail += 1
                await _mark_cant_dm(participant.id)
            except Exception:
                fail += 1
            await asyncio.sleep(0.12)
        except (TelegramForbiddenError, TelegramBadRequest):
            fail += 1
            await _mark_cant_dm(participant.id)
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
            await asyncio.sleep(0.05)

    async with AsyncSessionLocal() as session:
        session.add(
            Broadcast(
                giveaway_id=giveaway_id,
                text=text,
                created_at=datetime.now(timezone.utc),
                sent_ok=ok,
                sent_fail=fail,
            )
        )
        await session.commit()

    return ok, fail


async def _mark_cant_dm(participant_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Participant).where(Participant.id == participant_id).values(can_dm=False)
        )
        await session.commit()


async def broadcast_to_all_participants(
    bot: Bot, text: str, reply_markup: InlineKeyboardMarkup | None = None
) -> tuple[int, int]:
    ok = 0
    fail = 0
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(distinct(Participant.user_id)).where(Participant.can_dm == True)
        )
        user_ids = [row[0] for row in result.all()]

    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
            ok += 1
            await asyncio.sleep(0.12)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after))
            try:
                await bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
                ok += 1
            except (TelegramForbiddenError, TelegramBadRequest):
                fail += 1
                await _mark_cant_dm_by_user(user_id)
            except Exception:
                fail += 1
            await asyncio.sleep(0.12)
        except (TelegramForbiddenError, TelegramBadRequest):
            fail += 1
            await _mark_cant_dm_by_user(user_id)
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
            await asyncio.sleep(0.05)

    return ok, fail


async def _mark_cant_dm_by_user(user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Participant).where(Participant.user_id == user_id).values(can_dm=False)
        )
        await session.commit()
