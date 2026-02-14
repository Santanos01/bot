from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.handlers.common import AdminFilter
from app.services.broadcast_jobs import create_broadcast_job

router = Router()
router.message.filter(AdminFilter())


class BroadcastState(StatesGroup):
    organizer = State()
    text = State()


class BroadcastAllState(StatesGroup):
    organizer = State()
    text = State()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("broadcast:"))
async def start_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    await state.clear()
    await state.update_data(giveaway_id=giveaway_id)
    await state.set_state(BroadcastState.organizer)
    await callback.message.answer("Укажите организатора (например, @channelname):")
    await callback.answer()


@router.message(BroadcastState.organizer)
async def broadcast_organizer(message: Message, state: FSMContext) -> None:
    organizer = message.text.strip()
    await state.update_data(organizer=organizer)
    await state.set_state(BroadcastState.text)
    await message.answer("Введите текст рассылки:")


@router.message(BroadcastState.text)
async def send_broadcast(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    organizer = data.get("organizer") or ""
    if not giveaway_id:
        await message.answer("Не удалось определить розыгрыш.")
        await state.clear()
        return

    body = message.text.strip()
    job = await create_broadcast_job(body, organizer, giveaway_id, is_global=False)
    if not job:
        await message.answer("Такая рассылка уже в очереди.")
    else:
        await message.answer(f"Рассылка поставлена в очередь. ID: {job.id}")
    await state.clear()


@router.callback_query(AdminFilter(), lambda c: c.data == "admin:broadcast_all")
async def start_broadcast_all(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BroadcastAllState.organizer)
    await callback.message.answer("Укажите организатора (например, @channelname):")
    await callback.answer()


@router.message(BroadcastAllState.organizer)
async def broadcast_all_organizer(message: Message, state: FSMContext) -> None:
    organizer = message.text.strip()
    await state.update_data(organizer=organizer)
    await state.set_state(BroadcastAllState.text)
    await message.answer("Введите текст рассылки всем участникам:")


@router.message(BroadcastAllState.text)
async def send_broadcast_all(message: Message, state: FSMContext) -> None:
    organizer = (await state.get_data()).get("organizer") or ""
    body = message.text.strip()
    job = await create_broadcast_job(body, organizer, giveaway_id=None, is_global=True)
    if not job:
        await message.answer("Такая рассылка уже в очереди.")
    else:
        await message.answer(f"Глобальная рассылка поставлена в очередь. ID: {job.id}")
    await state.clear()
