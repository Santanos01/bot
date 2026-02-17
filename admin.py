from datetime import datetime, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from app.handlers.common import AdminFilter
from app.services.giveaways import create_giveaway, global_stats
from app.scheduler import schedule_giveaway_end
from app.keyboards import winners_mode_kb, publish_post_kb, admin_root_kb

router = Router()
router.message.filter(AdminFilter())


class NewGiveaway(StatesGroup):
    title = State()
    channel = State()
    winner_message = State()
    winners_mode = State()
    winners_count = State()
    ends_at = State()
    publish_post = State()
    post_text = State()
    post_photo = State()
    post_button = State()


class EditGiveaway(StatesGroup):
    field = State()


def _safe_input_text(message: Message) -> str | None:
    text = (message.text or message.caption or "").strip()
    return text or None


@router.message(Command("new"))
async def new_giveaway_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Введите название розыгрыша:")
    await state.set_state(NewGiveaway.title)


@router.callback_query(AdminFilter(), lambda c: c.data == "admin:new_giveaway")
async def new_giveaway_start_cb(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Введите название розыгрыша:")
    await state.set_state(NewGiveaway.title)
    await callback.answer()


@router.message(NewGiveaway.title)
async def new_giveaway_title(message: Message, state: FSMContext) -> None:
    text = _safe_input_text(message)
    if not text:
        await message.answer("Введите название розыгрыша текстом:")
        return
    await state.update_data(title=text)
    await message.answer("Укажите обязательный канал (например, @mychannel):")
    await state.set_state(NewGiveaway.channel)


@router.message(NewGiveaway.channel)
async def new_giveaway_channel(message: Message, state: FSMContext) -> None:
    channel = _safe_input_text(message)
    if not channel:
        await message.answer("Введите канал текстом (например, @mychannel):")
        return
    if not channel.startswith("@"):
        await message.answer("Канал должен начинаться с @. Попробуйте ещё раз:")
        return
    await state.update_data(channel=channel)
    await message.answer("Какое сообщение отправить победителю? (текст, или '-' чтобы пропустить):")
    await state.set_state(NewGiveaway.winner_message)


@router.message(NewGiveaway.winner_message)
async def new_giveaway_winner_message(message: Message, state: FSMContext) -> None:
    text = _safe_input_text(message)
    if text is None:
        await message.answer("Введите текст сообщения для победителя или '-' чтобы пропустить:")
        return
    await state.update_data(winner_message=None if text == "-" else text)
    await message.answer("Режим победителей: COUNT или ALL?", reply_markup=winners_mode_kb())
    await state.set_state(NewGiveaway.winners_mode)


@router.message(NewGiveaway.winners_mode)
async def new_giveaway_mode(message: Message, state: FSMContext) -> None:
    text = _safe_input_text(message)
    if not text:
        await message.answer("Укажите COUNT или ALL:")
        return
    mode = text.upper()
    if mode not in {"COUNT", "ALL"}:
        await message.answer("Укажите COUNT или ALL:")
        return
    await state.update_data(winners_mode=mode)
    if mode == "COUNT":
        await message.answer("Сколько победителей? (1-1000)")
        await state.set_state(NewGiveaway.winners_count)
    else:
        await state.update_data(winners_count=None)
        await message.answer("Когда завершить? Формат: YYYY-MM-DD HH:MM (UTC), или '-' для без таймера")
        await state.set_state(NewGiveaway.ends_at)


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("wmode:"))
async def new_giveaway_mode_cb(callback: CallbackQuery, state: FSMContext) -> None:
    mode = callback.data.split(":")[1]
    if mode not in {"COUNT", "ALL"}:
        await callback.answer("Неверный режим", show_alert=True)
        return
    await state.update_data(winners_mode=mode)
    if mode == "COUNT":
        await callback.message.answer("Сколько победителей? (1-1000)")
        await state.set_state(NewGiveaway.winners_count)
    else:
        await state.update_data(winners_count=None)
        await callback.message.answer("Когда завершить? Формат: YYYY-MM-DD HH:MM (UTC), или '-' для без таймера")
        await state.set_state(NewGiveaway.ends_at)
    await callback.answer()


@router.message(NewGiveaway.winners_count)
async def new_giveaway_count(message: Message, state: FSMContext) -> None:
    text = _safe_input_text(message)
    if not text:
        await message.answer("Введите число от 1 до 1000:")
        return
    try:
        count = int(text)
    except ValueError:
        await message.answer("Введите число от 1 до 1000:")
        return
    if count < 1 or count > 1000:
        await message.answer("Введите число от 1 до 1000:")
        return
    await state.update_data(winners_count=count)
    await message.answer("Когда завершить? Формат: YYYY-MM-DD HH:MM (UTC), или '-' для без таймера")
    await state.set_state(NewGiveaway.ends_at)


@router.message(NewGiveaway.ends_at)
async def new_giveaway_ends_at(message: Message, state: FSMContext) -> None:
    text = _safe_input_text(message)
    if text is None:
        await message.answer("Введите дату в формате YYYY-MM-DD HH:MM (UTC) или '-' :")
        return
    ends_at = None
    if text != "-":
        try:
            ends_at = datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            await message.answer("Неверный формат. Используйте YYYY-MM-DD HH:MM (UTC) или '-' :")
            return
    data = await state.get_data()
    giveaway = await create_giveaway(
        title=data["title"],
        description=None,
        channel_username=data["channel"],
        winner_message=data.get("winner_message"),
        winners_mode=data["winners_mode"],
        winners_count=data.get("winners_count"),
        ends_at=ends_at,
        created_by=message.from_user.id,
    )
    schedule_giveaway_end(giveaway.id, giveaway.ends_at)
    await state.clear()

    deep_link = f"https://t.me/{(await message.bot.me()).username}?start=gw_{giveaway.id}"
    await message.answer(
        "Розыгрыш создан!\n"
        f"ID: {giveaway.id}\n"
        f"Ссылка: {deep_link}\n\n"
        "Опубликовать пост в канале?",
        reply_markup=publish_post_kb(),
    )
    await state.update_data(
        giveaway_id=giveaway.id,
        deep_link=deep_link,
        channel_username=giveaway.channel_username,
    )
    await state.set_state(NewGiveaway.publish_post)


@router.message(NewGiveaway.publish_post)
async def new_giveaway_publish_post(message: Message, state: FSMContext) -> None:
    answer = _safe_input_text(message)
    if not answer:
        await message.answer("Ответьте 'да' или 'нет':")
        return
    answer = answer.lower()
    if answer not in {"да", "нет", "yes", "no"}:
        await message.answer("Ответьте 'да' или 'нет':")
        return
    if answer in {"нет", "no"}:
        await state.clear()
        return
    await message.answer("Введите текст поста для канала:")
    await state.set_state(NewGiveaway.post_text)


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("publish:"))
async def new_giveaway_publish_post_cb(callback: CallbackQuery, state: FSMContext) -> None:
    answer = callback.data.split(":")[1]
    if answer == "no":
        await state.clear()
        await callback.message.answer("Ок, пост не публикуем.")
        await callback.answer()
        return
    await callback.message.answer("Введите текст поста для канала:")
    await state.set_state(NewGiveaway.post_text)
    await callback.answer()


@router.message(NewGiveaway.post_text)
async def new_giveaway_post_text(message: Message, state: FSMContext) -> None:
    text = _safe_input_text(message)
    if not text:
        await message.answer("Введите текст поста текстовым сообщением:")
        return
    await state.update_data(post_text=text)
    await message.answer("Пришлите фото для поста (как изображение, не файл):")
    await state.set_state(NewGiveaway.post_photo)


@router.message(NewGiveaway.post_photo)
async def new_giveaway_post_photo(message: Message, state: FSMContext) -> None:
    if not message.photo:
        await message.answer("Нужно отправить фото. Попробуйте ещё раз:")
        return
    file_id = message.photo[-1].file_id
    await state.update_data(post_photo=file_id)
    await message.answer("Введите текст кнопки для поста:")
    await state.set_state(NewGiveaway.post_button)


@router.message(NewGiveaway.post_button)
async def new_giveaway_post_button(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    deep_link = data.get("deep_link")
    post_text = data.get("post_text")
    post_photo = data.get("post_photo")
    channel_username = data.get("channel_username")
    button_text = _safe_input_text(message)
    if not button_text:
        await message.answer("Введите текст кнопки:")
        return
    if not all([giveaway_id, deep_link, post_text, post_photo, button_text]):
        await message.answer("Не удалось подготовить пост. Попробуйте ещё раз.")
        await state.clear()
        return
    if not channel_username:
        from app.services.giveaways import get_giveaway
        giveaway = await get_giveaway(giveaway_id)
        channel_username = giveaway.channel_username if giveaway else None
    if not channel_username:
        await message.answer("Не удалось определить канал для публикации.")
        await state.clear()
        return

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from app.services.sender import send_photo_limited

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=deep_link)]
        ]
    )
    from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

    try:
        await send_photo_limited(
            message.bot,
            chat_id=channel_username,
            photo=post_photo,
            caption=post_text,
            reply_markup=kb,
        )
        await message.answer("Пост опубликован.")
    except (TelegramBadRequest, TelegramForbiddenError):
        await message.answer("Не удалось опубликовать пост. Проверьте, что бот админ в канале и канал доступен.")
    await state.clear()


@router.message(EditGiveaway.field)
async def edit_giveaway_field(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    giveaway_id = data.get("giveaway_id")
    field = data.get("field")
    if not giveaway_id or not field:
        await message.answer("Не удалось определить розыгрыш.")
        await state.clear()
        return

    from app.services.giveaways import update_giveaway_fields, get_giveaway

    text = _safe_input_text(message)
    if text is None:
        await message.answer("Ожидаю текстовый ввод. Попробуйте ещё раз.")
        return
    if field == "description":
        value = None if text == "-" else text
        await update_giveaway_fields(giveaway_id, description=value)
        await message.answer("Описание обновлено.")
    elif field == "ends_at":
        if text == "-":
            await update_giveaway_fields(giveaway_id, ends_at=None)
            await message.answer("Дата окончания удалена.")
        else:
            try:
                ends_at = datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except ValueError:
                await message.answer("Неверный формат. Используйте YYYY-MM-DD HH:MM (UTC) или '-' :")
                return
            await update_giveaway_fields(giveaway_id, ends_at=ends_at)
            schedule_giveaway_end(giveaway_id, ends_at)
            await message.answer("Дата окончания обновлена.")
    elif field == "winners_count":
        try:
            count = int(text)
        except ValueError:
            await message.answer("Введите число от 1 до 1000:")
            return
        if count < 1 or count > 1000:
            await message.answer("Введите число от 1 до 1000:")
            return
        giveaway = await get_giveaway(giveaway_id)
        if giveaway and giveaway.winners_mode == "ALL":
            await update_giveaway_fields(giveaway_id, winners_mode="COUNT", winners_count=count)
            await message.answer("Режим изменен на COUNT. Кол-во победителей обновлено.")
        else:
            await update_giveaway_fields(giveaway_id, winners_count=count)
            await message.answer("Кол-во победителей обновлено.")

    await state.clear()


@router.message(Command("admin"))
async def list_giveaways(message: Message) -> None:
    stats = await global_stats()
    text = (
        "Админ панель.\n\n"
        f"Всего розыгрышей: {stats['giveaways_total']}\n"
        f"Активных: {stats['giveaways_active']}\n"
        f"Завершённых: {stats['giveaways_finished']}\n"
        f"Уникальных участников: {stats['participants_total']}\n"
        f"Доступно для рассылки: {stats['participants_can_dm']}\n"
        f"Победителей всего: {stats['winners_total']}\n"
        f"Рассылок всего: {stats['broadcasts_total']}"
    )
    await message.answer(text, reply_markup=admin_root_kb())


@router.message(lambda m: bool(m.photo))
async def admin_photo_fallback(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current == NewGiveaway.post_photo.state:
        return
    await message.answer(
        "Нет активного шага загрузки фото. "
        "Если бот перезапускался, начните заново: /new"
    )
