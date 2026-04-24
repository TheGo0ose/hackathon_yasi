"""
Keyboard builders for the credit scoring bot.
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

from config import WEB_APP_URL


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu with Mini App button and quick-score option."""
    buttons = [
        [
            InlineKeyboardButton(
                text="🌐 Открыть скоринг",
                web_app=WebAppInfo(url=WEB_APP_URL),
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 Быстрый скоринг в чате",
                callback_data="start_scoring",
            ),
        ],
        [
            InlineKeyboardButton(
                text="💬 AI-советник",
                callback_data="start_advisor",
            ),
        ],
        [
            InlineKeyboardButton(
                text="ℹ️ О проекте",
                callback_data="about",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel button during scoring flow."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Return to main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")],
        ]
    )


def score_again_keyboard() -> InlineKeyboardMarkup:
    """After scoring — score again, advisor, or open Mini App."""
    buttons = [
        [
            InlineKeyboardButton(
                text="💬 Спросить AI-советника",
                callback_data="advisor_after_score",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔄 Новая заявка",
                callback_data="start_scoring",
            ),
        ],
        [
            InlineKeyboardButton(
                text="🌐 Подробнее на сайте",
                web_app=WebAppInfo(url=WEB_APP_URL),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🔙 Главное меню",
                callback_data="main_menu",
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def advisor_keyboard() -> InlineKeyboardMarkup:
    """During advisor chat — exit button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Завершить чат", callback_data="exit_advisor")],
        ]
    )
