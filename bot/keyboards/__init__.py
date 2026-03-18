from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.config import settings


def main_menu_keyboard(has_subscription: bool = False, show_trial: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    buttons = []

    if has_subscription:
        buttons.append([
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")
        ])
        buttons.append([
            InlineKeyboardButton(text="📖 Инструкция", callback_data="show_instruction")
        ])
    else:
        if show_trial:
            buttons.append([
                InlineKeyboardButton(text="🎁 Попробовать бесплатно (3 часа)", callback_data="get_trial")
            ])
        buttons.append([
            InlineKeyboardButton(
                text=f"⭐ Купить подписку ({settings.subscription_price_stars} Star)",
                callback_data="buy_subscription"
            )
        ])
        buttons.append([
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")
        ])
        buttons.append([
            InlineKeyboardButton(text="📖 Инструкция", callback_data="show_instruction")
        ])

    buttons.append([
        InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/WhiteLisVPN")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_keyboard(has_subscription: bool = False, config_url: str = None) -> InlineKeyboardMarkup:
    """Profile keyboard."""
    buttons = []

    if has_subscription and config_url:
        buttons.append([
            InlineKeyboardButton(text="📋 Скопировать ссылку", copy_text={"text": config_url})
        ])

    if not has_subscription:
        buttons.append([
            InlineKeyboardButton(
                text=f"⭐ Купить подписку ({settings.subscription_price_stars} Star)",
                callback_data="buy_subscription"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_keyboard() -> InlineKeyboardMarkup:
    """Back to menu keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
    ])
