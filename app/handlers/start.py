from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.keyboards import giveaway_user_kb
from app.services.giveaways import get_giveaway
from app.services.users import upsert_user

router = Router()


@router.message(CommandStart(deep_link=True))
async def start_with_deep_link(message: Message) -> None:
    await upsert_user(message.from_user.id, message.from_user.username)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Добро пожаловать! Используйте ссылку на розыгрыш, чтобы участвовать.")
        return
    payload = args[1]
    if not payload.startswith("gw_"):
        await message.answer("Добро пожаловать! Используйте ссылку на розыгрыш, чтобы участвовать.")
        return
    try:
        giveaway_id = int(payload.replace("gw_", ""))
    except ValueError:
        await message.answer("Некорректная ссылка на розыгрыш.")
        return

    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        await message.answer("Розыгрыш не найден.")
        return

    text = (
        f"🎁 <b>{giveaway.title}</b>\n\n"
        f"Организатор: {giveaway.channel_username}\n"
    )
    await message.answer(text, reply_markup=giveaway_user_kb(giveaway.id))


@router.message(CommandStart())
async def start(message: Message) -> None:
    await upsert_user(message.from_user.id, message.from_user.username)
    await message.answer("Привет! Чтобы участвовать в розыгрыше, откройте ссылку приглашения.")
