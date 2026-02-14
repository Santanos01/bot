from aiogram import Router
from aiogram.filters import Filter
from aiogram.types import Message, CallbackQuery
from app.config.config import settings


class AdminFilter(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if event.from_user else 0
        return user_id in settings.admins


router = Router()
