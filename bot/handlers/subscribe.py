from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto,
    FSInputFile,
)
from datetime import timedelta
from pathlib import Path

from core.database import db
from core.config import settings
from core.utils import generate_payment_payload
from bot.keyboards import back_keyboard

router = Router()


def success_keyboard(config_url: str) -> InlineKeyboardMarkup:
    """Keyboard with copy link and menu buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ссылку", copy_text={"text": config_url})],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="show_instruction")],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
    ])


INSTRUCTION_TEXT = """
⌨️ *Инструкция по подключению V2Box*

1. Скопируйте VPN-ссылку, которую прислал бот
2. Скачайте приложение V2Box:
   • [iPhone — App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690)
   • [Android — Google Play](https://play.google.com/store/apps/details?id=dev.hexasoftware.v2box)
3. Откройте приложение V2Box
4. Нажмите кнопку *+*
5. Выберите *«Import URL from clipboard»*
6. Ссылка добавится автоматически
7. Выберите сервер без надписи timeout
8. Включите подключение (Connect)
9. Пользуйтесь VPN при включённых белых списках и мобильном интернете

*Если соединение пропало:*
• Зайдите в список серверов
• Выберите сервер с зелёным минимальным пингом
• Подключитесь заново

*Если у всех серверов timeout:*
• Откройте добавленную ссылку внутри приложения
• Нажмите значок обновления
• Дождитесь обновления серверов
• Попробуйте подключиться снова
"""


@router.callback_query(F.data == "show_instruction")
async def show_instruction(callback: CallbackQuery):
    """Show detailed instruction with images."""
    # Get media directory path
    media_dir = Path(__file__).parent.parent / "media"

    # Send instruction images as media group
    media_group = [
        InputMediaPhoto(media=FSInputFile(media_dir / "instruction_1.jpg")),
        InputMediaPhoto(media=FSInputFile(media_dir / "instruction_2.jpg")),
        InputMediaPhoto(media=FSInputFile(media_dir / "instruction_3.jpg")),
    ]

    await callback.message.answer_media_group(media=media_group)

    # Send instruction text
    await callback.message.answer(
        INSTRUCTION_TEXT.strip(),
        parse_mode="Markdown",
        reply_markup=back_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "buy_subscription")
async def buy_subscription(callback: CallbackQuery):
    """Send invoice for subscription purchase."""
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if not user:
        await callback.answer("Ошибка: пользователь не найден", show_alert=True)
        return

    # Check if already has subscription
    if await db.has_active_subscription(user.id):
        await callback.answer("У вас уже есть активная подписка!", show_alert=True)
        return

    payload = generate_payment_payload()

    await callback.message.answer_invoice(
        title="WhiteLis VPN Подписка",
        description=f"Подписка на {settings.subscription_days} дней. Доступ к VPN для обхода блокировок.",
        payload=payload,
        currency="XTR",  # Telegram Stars
        prices=[
            LabeledPrice(label="Подписка", amount=settings.subscription_price_stars)
        ],
    )

    await callback.answer()


@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout: PreCheckoutQuery):
    """Handle pre-checkout query - approve the payment."""
    await pre_checkout.answer(ok=True)


@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    """Handle successful payment - activate subscription."""
    payment = message.successful_payment

    user = await db.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Ошибка: пользователь не найден. Обратитесь в поддержку.")
        return

    # Create subscription
    subscription = await db.create_subscription(
        user_id=user.id,
        stars_paid=payment.total_amount,
        telegram_payment_id=payment.telegram_payment_charge_id
    )

    config_url = f"{settings.base_url}/config/{user.config_token}"

    # Moscow timezone (UTC+3)
    expires_msk = subscription.expires_at + timedelta(hours=3)

    success_text = f"""
✅ *Оплата прошла успешно!*

📅 Подписка активна до: *{expires_msk.strftime('%d.%m.%Y %H:%M')}* (UTC+3)

🔗 Ваша ссылка:
`{config_url}`

👆 Нажмите на ссылку чтобы скопировать, или используйте кнопку ниже.
"""

    await message.answer(
        success_text.strip(),
        reply_markup=success_keyboard(config_url),
        parse_mode="Markdown"
    )
