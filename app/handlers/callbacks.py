from aiogram import Router
from datetime import timedelta
from aiogram.types import CallbackQuery

from app.handlers.common import AdminFilter
from app.keyboards import (
    giveaway_user_kb,
    not_subscribed_kb,
    admin_giveaway_kb,
    back_to_giveaway_kb,
    confirm_delete_kb,
)
from app.services.giveaways import (
    get_giveaway,
    check_subscription,
    add_participant,
    get_participant,
    participants_count,
    winners_count,
    broadcasts_count,
    list_participants,
    finalize_and_notify,
    delete_giveaway,
)
from aiogram.fsm.context import FSMContext
from app.handlers.admin import EditGiveaway

router = Router()


@router.callback_query(lambda c: c.data.startswith("join:"))
async def join_giveaway(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    if giveaway.status != "ACTIVE":
        await callback.answer("Розыгрыш уже завершён.", show_alert=True)
        return

    is_subscribed = await check_subscription(callback.bot, giveaway.channel_username, callback.from_user.id)
    if not is_subscribed:
        await callback.message.edit_reply_markup(
            reply_markup=not_subscribed_kb(giveaway.channel_username, giveaway.id)
        )
        await callback.answer("Подпишитесь на канал и нажмите Проверить подписку", show_alert=True)
        return

    added = await add_participant(giveaway.id, callback.from_user.id, callback.from_user.username)
    if added:
        participant = await get_participant(giveaway.id, callback.from_user.id)
        ticket = participant.ticket_number if participant else "—"
        winners_info = "10"
        if giveaway.ends_at:
            msk_time = giveaway.ends_at + timedelta(hours=3)
            ends_at = msk_time.strftime("%d.%m.%Y")
        else:
            ends_at = "Не задана"
        organizer_name = giveaway.channel_username.lstrip("@")
        organizer_link = f"https://t.me/{organizer_name}"
        text = (
            "🎁 <b>Вы успешно зарегистрированы на розыгрыш от организатора:</b>\n"
            f"<a href=\"{organizer_link}\">{organizer_name}</a>\n\n"
            f"🎫 <b>Номер вашего билета:</b> #{ticket}\n"
            f"🏆 <b>Количество призовых мест:</b> {winners_info}\n\n"
            f"⏳ <b>Дата подведения итогов:</b> {ends_at}\n\n"
            "⚠️ <b>Важно:</b> не удаляйте и не блокируйте бота — иначе мы не сможем уведомить вас о результате."
        )
        await callback.message.answer(text)
        await callback.answer("Вы участвуете в розыгрыше!", show_alert=True)
    else:
        await callback.answer("Вы уже участвуете.", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("check:"))
async def check_sub(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return

    is_subscribed = await check_subscription(callback.bot, giveaway.channel_username, callback.from_user.id)
    if is_subscribed:
        try:
            await callback.message.edit_reply_markup(reply_markup=giveaway_user_kb(giveaway.id))
        except Exception:
            pass
        await callback.answer("Подписка подтверждена. Теперь участвуйте.", show_alert=True)
    else:
        try:
            await callback.message.edit_reply_markup(
                reply_markup=not_subscribed_kb(giveaway.channel_username, giveaway.id)
            )
        except Exception:
            pass
        await callback.answer("Подписка не найдена.", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("rules:"))
async def rules(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return

    text = (
        f"Правила розыгрыша:\n"
        f"1) Подпишитесь на канал {giveaway.channel_username}\n"
        f"2) Нажмите 'Участвовать'\n"
        f"3) Дождитесь завершения."
    )
    await callback.answer()
    await callback.message.answer(text)


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("admin:") and c.data.split(":")[1].isdigit())
async def admin_panel(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    count = await participants_count(giveaway_id)
    await callback.message.answer(
        f"Админ панель розыгрыша #{giveaway.id} — {giveaway.title}",
        reply_markup=admin_giveaway_kb(giveaway.id, count),
    )
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("participants:"))
async def participants(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    participants_list = await list_participants(giveaway_id)
    count = len(participants_list)
    if count == 0:
        await callback.message.answer("Участников пока нет.", reply_markup=back_to_giveaway_kb(giveaway_id))
        await callback.answer()
        return
    preview = "\n".join(
        [f"- {p.user_id} @{p.username}" if p.username else f"- {p.user_id}" for p in participants_list[:50]]
    )
    more = "\n..." if count > 50 else ""
    await callback.message.answer(
        f"Участники ({count}):\n{preview}{more}",
        reply_markup=back_to_giveaway_kb(giveaway_id),
    )
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("pick:"))
async def pick(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    winners, ok, fail = await finalize_and_notify(callback.bot, giveaway_id)
    if not winners:
        await callback.message.answer("Победителей нет (возможно, нет участников).")
        await callback.answer()
        return
    winners_list = "\n".join([str(u) for u in winners])
    await callback.message.answer(f"Победители:\n{winners_list}\n\nУведомления: OK {ok} / FAIL {fail}")
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("finish:"))
async def finish(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    winners, ok, fail = await finalize_and_notify(callback.bot, giveaway_id)
    if not winners:
        await callback.message.answer("Розыгрыш завершен. Победителей нет.")
    else:
        await callback.message.answer(f"Розыгрыш завершен. Победители выбраны.\nУведомления: OK {ok} / FAIL {fail}")
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("edit_desc:"))
async def edit_desc(callback: CallbackQuery, state: FSMContext) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    await state.clear()
    await state.update_data(giveaway_id=giveaway_id, field="description")
    await state.set_state(EditGiveaway.field)
    await callback.message.answer("Введите новое описание (или '-' чтобы очистить):")
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("edit_end:"))
async def edit_end(callback: CallbackQuery, state: FSMContext) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    await state.clear()
    await state.update_data(giveaway_id=giveaway_id, field="ends_at")
    await state.set_state(EditGiveaway.field)
    await callback.message.answer("Введите новую дату в формате YYYY-MM-DD HH:MM (UTC) или '-' чтобы убрать таймер:")
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("edit_wcount:"))
async def edit_wcount(callback: CallbackQuery, state: FSMContext) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    await state.clear()
    await state.update_data(giveaway_id=giveaway_id, field="winners_count")
    await state.set_state(EditGiveaway.field)
    await callback.message.answer("Введите новое кол-во победителей (1-1000):")
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("link:"))
async def regen_link(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    bot_username = (await callback.bot.me()).username
    deep_link = f"https://t.me/{bot_username}?start=gw_{giveaway_id}"
    await callback.message.answer(f"Ссылка на розыгрыш:\n{deep_link}")
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("summary:"))
async def summary(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    giveaway = await get_giveaway(giveaway_id)
    if not giveaway:
        await callback.answer("Розыгрыш не найден", show_alert=True)
        return
    count = await participants_count(giveaway_id)
    wcount = await winners_count(giveaway_id)
    bcount = await broadcasts_count(giveaway_id)
    ends = giveaway.ends_at.isoformat() if giveaway.ends_at else "—"
    text = (
        f"Сводка #{giveaway.id}\n"
        f"Название: {giveaway.title}\n"
        f"Статус: {giveaway.status}\n"
        f"Канал: {giveaway.channel_username}\n"
        f"Режим: {giveaway.winners_mode}\n"
        f"Кол-во победителей: {giveaway.winners_count or '—'}\n"
        f"Участников: {count}\n"
        f"Победителей: {wcount}\n"
        f"Рассылок: {bcount}\n"
        f"Окончание (UTC): {ends}"
    )
    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("delete:"))
async def delete_prompt(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    await callback.message.answer("Подтвердите удаление розыгрыша:", reply_markup=confirm_delete_kb(giveaway_id))
    await callback.answer()


@router.callback_query(AdminFilter(), lambda c: c.data.startswith("delete_confirm:"))
async def delete_confirm(callback: CallbackQuery) -> None:
    giveaway_id = int(callback.data.split(":")[1])
    await delete_giveaway(giveaway_id)
    await callback.message.answer("Розыгрыш удалён.")
    await callback.answer()
