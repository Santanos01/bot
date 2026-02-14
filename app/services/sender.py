import logging
import asyncio
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup
from app.utils.ratelimiter import RateLimiter, RateLimits

logger = logging.getLogger(__name__)

_limits = RateLimiter(RateLimits())


async def send_message_limited(
    bot: Bot,
    chat_id: int | str,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    user_id: int | None = None,
) -> None:
    if isinstance(chat_id, str):
        chat_key = hash(chat_id)
    else:
        chat_key = int(chat_id)
    await _limits.acquire(chat_id=chat_key, user_id=user_id)
    try:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    except TelegramRetryAfter as e:
        logger.warning("RetryAfter %s sec for chat %s", e.retry_after, chat_id)
        await asyncio.sleep(float(e.retry_after))
        await _limits.acquire(chat_id=chat_key, user_id=user_id)
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


async def send_photo_limited(
    bot: Bot,
    chat_id: int | str,
    photo: str,
    caption: str | None = None,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> None:
    if isinstance(chat_id, str):
        chat_key = hash(chat_id)
    else:
        chat_key = int(chat_id)
    await _limits.acquire(chat_id=chat_key, user_id=None)
    try:
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
    except TelegramRetryAfter as e:
        logger.warning("RetryAfter %s sec for chat %s", e.retry_after, chat_id)
        await asyncio.sleep(float(e.retry_after))
        await _limits.acquire(chat_id=chat_key, user_id=None)
        await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=reply_markup)
