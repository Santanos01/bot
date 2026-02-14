import re
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

_USERNAME_RE = re.compile(r"@([A-Za-z0-9_]{5,32})")


def contact_button_markup(text: str) -> InlineKeyboardMarkup | None:
    match = _USERNAME_RE.search(text)
    if not match:
        return None
    username = match.group(1)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Связаться", url=f"https://t.me/{username}")]
        ]
    )
