import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

from core.config import settings
from core.database import db
from bot.handlers import setup_routers
from bot.middleware import ThrottlingMiddleware


EXPIRED_TRIAL_TEXT = """
⏰ *Ваш пробный период закончился!*

Понравился VPN? Оформите подписку чтобы продолжить пользоваться сервисом.

⭐ Подписка на 30 дней — {price} Stars
"""

EXPIRED_SUB_TEXT = """
⏰ *Ваша подписка закончилась!*

Продлите подписку чтобы продолжить пользоваться VPN.

⭐ Подписка на 30 дней — {price} Stars
"""


def expired_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"⭐ Купить подписку ({settings.subscription_price_stars} Stars)",
            callback_data="buy_subscription"
        )],
        [InlineKeyboardButton(text="🏠 В меню", callback_data="back_to_menu")]
    ])


async def check_expired_subscriptions(bot: Bot, logger: logging.Logger):
    """Background task to notify users about expired subscriptions."""
    while True:
        try:
            expired = await db.get_expired_unnotified_subscriptions()

            for sub in expired:
                try:
                    if sub["is_trial"]:
                        text = EXPIRED_TRIAL_TEXT.format(price=settings.subscription_price_stars)
                    else:
                        text = EXPIRED_SUB_TEXT.format(price=settings.subscription_price_stars)

                    await bot.send_message(
                        chat_id=sub["telegram_id"],
                        text=text.strip(),
                        parse_mode="Markdown",
                        reply_markup=expired_keyboard()
                    )
                    await db.mark_subscription_notified(sub["id"])
                    logger.info(f"Sent expiration notification to {sub['telegram_id']}")

                except Exception as e:
                    logger.error(f"Failed to notify {sub['telegram_id']}: {e}")
                    await db.mark_subscription_notified(sub["id"])

        except Exception as e:
            logger.error(f"Error in expiration checker: {e}")

        await asyncio.sleep(60)  # Check every minute


async def main():
    """Main bot entry point."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout,
    )
    logger = logging.getLogger(__name__)

    # Initialize database
    await db.connect()
    logger.info("Database connected")

    # Initialize bot
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # Setup dispatcher
    dp = Dispatcher()

    # Add throttling middleware (1 second rate limit)
    dp.message.middleware(ThrottlingMiddleware(rate_limit=1.0))
    dp.callback_query.middleware(ThrottlingMiddleware(rate_limit=0.5))

    dp.include_router(setup_routers())

    # Set bot commands menu
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="profile", description="Мой профиль"),
        BotCommand(command="subscribe", description="Купить подписку"),
        BotCommand(command="instruction", description="Инструкция"),
        BotCommand(command="support", description="Поддержка"),
    ])

    logger.info("Starting bot...")

    # Start background task for expiration notifications
    asyncio.create_task(check_expired_subscriptions(bot, logger))

    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
