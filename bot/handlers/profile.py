from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from datetime import datetime, timedelta, timezone

from core.database import db
from core.config import settings
from bot.keyboards import profile_keyboard

router = Router()


async def get_profile_text_and_url(telegram_id: int):
    """Get profile text and config URL for user."""
    user = await db.get_user_by_telegram_id(telegram_id)

    if not user:
        return None, None, False

    subscription = await db.get_active_subscription(user.id)
    config_url = f"{settings.base_url}/config/{user.config_token}"

    if subscription:
        # Moscow timezone (UTC+3)
        expires_msk = subscription.expires_at + timedelta(hours=3)

        time_diff = subscription.expires_at - datetime.now()
        total_hours = int(time_diff.total_seconds() // 3600)
        days_left = total_hours // 24
        hours_left = total_hours % 24

        if days_left > 0:
            time_left = f"{days_left} дн. {hours_left} ч."
        else:
            time_left = f"{total_hours} ч."

        profile_text = f"""
👤 *Ваш профиль*

✅ Подписка: *Активна*
⏳ Осталось: *{time_left}*
📅 До: *{expires_msk.strftime('%d.%m.%Y %H:%M')}* (UTC+3)

🔗 Ваша ссылка:
`{config_url}`

👆 Нажмите на ссылку чтобы скопировать
"""
        return profile_text, config_url, True
    else:
        profile_text = """
👤 *Ваш профиль*

❌ Подписка: *Не активна*

Купите подписку, чтобы получить доступ к VPN.
"""
        return profile_text, None, False


async def show_profile_message(message: Message):
    """Show profile via message command."""
    profile_text, config_url, has_sub = await get_profile_text_and_url(message.from_user.id)

    if profile_text is None:
        await message.answer("Ошибка: пользователь не найден")
        return

    await message.answer(
        profile_text.strip(),
        reply_markup=profile_keyboard(has_sub, config_url),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Show user profile."""
    profile_text, config_url, has_sub = await get_profile_text_and_url(callback.from_user.id)

    if profile_text is None:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        profile_text.strip(),
        reply_markup=profile_keyboard(has_sub, config_url),
        parse_mode="Markdown"
    )
    await callback.answer()
