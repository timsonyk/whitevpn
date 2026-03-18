from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import datetime, timedelta, timezone

from core.database import db
from core.config import settings
from bot.keyboards import profile_keyboard

router = Router()


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    """Show user profile."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    subscription = await db.get_active_subscription(user.id)
    config_url = f"{settings.base_url}/config/{user.config_token}"

    if subscription:
        # Moscow timezone (UTC+3)
        msk_tz = timezone(timedelta(hours=3))
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
    else:
        profile_text = f"""
👤 *Ваш профиль*

❌ Подписка: *Не активна*

Купите подписку, чтобы получить доступ к VPN.
"""
        config_url = None

    await callback.message.edit_text(
        profile_text.strip(),
        reply_markup=profile_keyboard(subscription is not None, config_url),
        parse_mode="Markdown"
    )
    await callback.answer()
