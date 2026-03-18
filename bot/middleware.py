from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    """Middleware to prevent spam by rate limiting user actions."""

    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize throttling middleware.

        Args:
            rate_limit: Minimum seconds between actions per user
        """
        self.cache = TTLCache(maxsize=10000, ttl=rate_limit)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Get user id from event
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        else:
            return await handler(event, data)

        # Check if user is throttled
        if user_id in self.cache:
            # User is spamming - ignore silently
            if isinstance(event, CallbackQuery):
                await event.answer("Подождите немного...")
            return None

        # Mark user as recently active
        self.cache[user_id] = True

        return await handler(event, data)
