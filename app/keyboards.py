from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def giveaway_user_kb(giveaway_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Участвовать", callback_data=f"join:{giveaway_id}")],
            [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data=f"check:{giveaway_id}")],
            [InlineKeyboardButton(text="📜 Правила", callback_data=f"rules:{giveaway_id}")],
        ]
    )


def not_subscribed_kb(channel_username: str, giveaway_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data=f"check:{giveaway_id}")],
            [InlineKeyboardButton(text="Открыть канал", url=f"https://t.me/{channel_username.lstrip('@')}")],
        ]
    )


def admin_giveaway_kb(giveaway_id: int, participants_count: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"👥 Участники ({participants_count})", callback_data=f"participants:{giveaway_id}")],
            [InlineKeyboardButton(text="🎲 Выбрать победителей", callback_data=f"pick:{giveaway_id}")],
            [InlineKeyboardButton(text="⏹ Завершить сейчас", callback_data=f"finish:{giveaway_id}")],
            [InlineKeyboardButton(text="📣 Рассылка участникам", callback_data=f"broadcast:{giveaway_id}")],
            [InlineKeyboardButton(text="📝 Изменить описание", callback_data=f"edit_desc:{giveaway_id}")],
            [InlineKeyboardButton(text="⏰ Изменить дату окончания", callback_data=f"edit_end:{giveaway_id}")],
            [InlineKeyboardButton(text="#️⃣ Изменить кол-во победителей", callback_data=f"edit_wcount:{giveaway_id}")],
            [InlineKeyboardButton(text="🔁 Сгенерировать новую ссылку", callback_data=f"link:{giveaway_id}")],
            [InlineKeyboardButton(text="📊 Статус/сводка", callback_data=f"summary:{giveaway_id}")],
            [InlineKeyboardButton(text="🗑 Удалить конкурс", callback_data=f"delete:{giveaway_id}")],
        ]
    )


def back_to_giveaway_kb(giveaway_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=f"admin:{giveaway_id}")],
        ]
    )


def confirm_delete_kb(giveaway_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, удалить", callback_data=f"delete_confirm:{giveaway_id}")],
            [InlineKeyboardButton(text="Отмена", callback_data=f"admin:{giveaway_id}")],
        ]
    )


def winners_mode_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="COUNT", callback_data="wmode:COUNT")],
            [InlineKeyboardButton(text="ALL", callback_data="wmode:ALL")],
        ]
    )


def publish_post_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="publish:yes")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="publish:no")],
        ]
    )


def admin_root_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать розыгрыш", callback_data="admin:new_giveaway")],
            [InlineKeyboardButton(text="📣 Рассылка всем участникам", callback_data="admin:broadcast_all")],
        ]
    )
