from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import config

def get_show_text_kb(message_id: int) -> InlineKeyboardMarkup:
    """
    Render a inline button "show text".
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=config.UI.BTN_SHOW,
            callback_data=f"show_{message_id}"
        )
    )
    return builder.as_markup()

def get_hide_text_kb(message_id: int) -> InlineKeyboardMarkup:
    """
    Render a inline button "hide text".
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=config.UI.BTN_HIDE,
            callback_data=f"hide_{message_id}"
        )
    )
    return builder.as_markup()