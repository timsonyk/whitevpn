from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from core.database import db
from core.config import settings
from bot.keyboards import main_menu_keyboard

ADMIN_IDS = [389481960]  # Твой Telegram ID

router = Router()


WELCOME_TEXT = """
🔐 *WhiteLis VPN*

VPN против белых списков для России.
Работает везде, даже в центре Москвы!

✅ Telegram, банки, ChatGPT, Яндекс, Instagram — всё работает!

⭐ Подписка — доступ к автообновляемым конфигам для V2Box (Android/iOS).

💬 Поддержка: @WhiteLisVPN
"""

TRIAL_TEXT = """
🎁 *Вам подарен пробный период на 3 часа!*

🔗 Ваша ссылка:
`{config_url}`

👆 Нажмите чтобы скопировать, затем вставьте в V2Box как подписку.
"""


def trial_keyboard(config_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ссылку", copy_text={"text": config_url})],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="show_instruction")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
    ])


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    # Get or create user
    user = await db.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )

    has_subscription = await db.has_active_subscription(user.id)
    has_had_trial = await db.has_ever_had_subscription(user.id)

    await message.answer(
        WELCOME_TEXT.strip(),
        reply_markup=main_menu_keyboard(has_subscription, show_trial=not has_had_trial),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "get_trial")
async def get_trial(callback: CallbackQuery):
    """Handle trial button click."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    # Check if already had trial
    if await db.has_ever_had_subscription(user.id):
        await callback.answer("Вы уже использовали пробный период!", show_alert=True)
        return

    # Create trial subscription
    await db.create_trial_subscription(user.id, hours=3)

    config_url = f"{settings.base_url}/config/{user.config_token}"

    await callback.message.edit_text(
        TRIAL_TEXT.format(config_url=config_url).strip(),
        reply_markup=trial_keyboard(config_url),
        parse_mode="Markdown"
    )
    await callback.answer("Пробный период активирован!")


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    """Handle back to menu button."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if user:
        has_subscription = await db.has_active_subscription(user.id)
        has_had_trial = await db.has_ever_had_subscription(user.id)
    else:
        has_subscription = False
        has_had_trial = True

    await callback.message.edit_text(
        WELCOME_TEXT.strip(),
        reply_markup=main_menu_keyboard(has_subscription, show_trial=not has_had_trial),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show bot statistics (admin only)."""
    if message.from_user.id not in ADMIN_IDS:
        return

    stats = await db.get_stats()

    stats_text = f"""
📊 *Статистика бота*

👥 Всего пользователей: *{stats['total_users']}*
🎁 Активировали триал: *{stats['trial_users']}*
💰 Оплатили подписку: *{stats['paid_users']}*
✅ Активных подписок: *{stats['active_subs']}*
"""

    await message.answer(stats_text.strip(), parse_mode="Markdown")
