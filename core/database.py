import aiosqlite
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .config import settings
from .utils import generate_token


@dataclass
class User:
    id: int
    telegram_id: int
    username: Optional[str]
    created_at: datetime
    config_token: str


@dataclass
class Subscription:
    id: int
    user_id: int
    starts_at: datetime
    expires_at: datetime
    stars_paid: int
    telegram_payment_id: Optional[str]


class Database:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self):
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._create_tables()

    async def close(self):
        if self._conn:
            await self._conn.close()

    async def _create_tables(self):
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                config_token TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                starts_at DATETIME NOT NULL,
                expires_at DATETIME NOT NULL,
                stars_paid INTEGER NOT NULL,
                telegram_payment_id TEXT,
                notified INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
            CREATE INDEX IF NOT EXISTS idx_users_config_token ON users(config_token);
            CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
        """)
        await self._conn.commit()

        # Add notified column if not exists (migration)
        try:
            await self._conn.execute("ALTER TABLE subscriptions ADD COLUMN notified INTEGER DEFAULT 0")
            await self._conn.commit()
        except:
            pass  # Column already exists

    async def get_or_create_user(self, telegram_id: int, username: Optional[str] = None) -> User:
        """Get existing user or create a new one."""
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()

        if row:
            return User(
                id=row["id"],
                telegram_id=row["telegram_id"],
                username=row["username"],
                created_at=datetime.fromisoformat(row["created_at"]),
                config_token=row["config_token"]
            )

        # Create new user
        token = generate_token()
        cursor = await self._conn.execute(
            "INSERT INTO users (telegram_id, username, config_token) VALUES (?, ?, ?)",
            (telegram_id, username, token)
        )
        await self._conn.commit()

        return User(
            id=cursor.lastrowid,
            telegram_id=telegram_id,
            username=username,
            created_at=datetime.now(),
            config_token=token
        )

    async def get_user_by_token(self, token: str) -> Optional[User]:
        """Get user by config token."""
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE config_token = ?",
            (token,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            created_at=datetime.fromisoformat(row["created_at"]),
            config_token=row["config_token"]
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        cursor = await self._conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return User(
            id=row["id"],
            telegram_id=row["telegram_id"],
            username=row["username"],
            created_at=datetime.fromisoformat(row["created_at"]),
            config_token=row["config_token"]
        )

    async def create_trial_subscription(self, user_id: int, hours: int = 0, minutes: int = 0) -> Subscription:
        """Create a trial subscription for new user."""
        starts_at = datetime.now()
        if minutes:
            expires_at = starts_at + timedelta(minutes=minutes)
        else:
            expires_at = starts_at + timedelta(hours=hours or 3)

        cursor = await self._conn.execute(
            """INSERT INTO subscriptions
               (user_id, starts_at, expires_at, stars_paid, telegram_payment_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, starts_at.isoformat(), expires_at.isoformat(), 0, "TRIAL")
        )
        await self._conn.commit()

        return Subscription(
            id=cursor.lastrowid,
            user_id=user_id,
            starts_at=starts_at,
            expires_at=expires_at,
            stars_paid=0,
            telegram_payment_id="TRIAL"
        )

    async def has_ever_had_subscription(self, user_id: int) -> bool:
        """Check if user ever had any subscription (including expired)."""
        cursor = await self._conn.execute(
            "SELECT COUNT(*) as cnt FROM subscriptions WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()
        return row["cnt"] > 0

    async def create_subscription(
        self,
        user_id: int,
        stars_paid: int,
        days: int = None,
        telegram_payment_id: str = None
    ) -> Subscription:
        """Create a new subscription for user."""
        days = days or settings.subscription_days
        starts_at = datetime.now()
        expires_at = starts_at + timedelta(days=days)

        cursor = await self._conn.execute(
            """INSERT INTO subscriptions
               (user_id, starts_at, expires_at, stars_paid, telegram_payment_id)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, starts_at.isoformat(), expires_at.isoformat(), stars_paid, telegram_payment_id)
        )
        await self._conn.commit()

        return Subscription(
            id=cursor.lastrowid,
            user_id=user_id,
            starts_at=starts_at,
            expires_at=expires_at,
            stars_paid=stars_paid,
            telegram_payment_id=telegram_payment_id
        )

    async def get_active_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get active subscription for user."""
        cursor = await self._conn.execute(
            """SELECT * FROM subscriptions
               WHERE user_id = ? AND expires_at > ?
               ORDER BY expires_at DESC LIMIT 1""",
            (user_id, datetime.now().isoformat())
        )
        row = await cursor.fetchone()

        if not row:
            return None

        return Subscription(
            id=row["id"],
            user_id=row["user_id"],
            starts_at=datetime.fromisoformat(row["starts_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
            stars_paid=row["stars_paid"],
            telegram_payment_id=row["telegram_payment_id"]
        )

    async def has_active_subscription(self, user_id: int) -> bool:
        """Check if user has active subscription."""
        sub = await self.get_active_subscription(user_id)
        return sub is not None

    async def has_active_subscription_by_token(self, token: str) -> bool:
        """Check if user with given token has active subscription."""
        user = await self.get_user_by_token(token)
        if not user:
            return False
        return await self.has_active_subscription(user.id)

    async def get_stats(self) -> dict:
        """Get bot statistics."""
        cursor = await self._conn.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]

        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE telegram_payment_id = 'TRIAL'"
        )
        trial_users = (await cursor.fetchone())[0]

        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE telegram_payment_id != 'TRIAL' AND telegram_payment_id IS NOT NULL"
        )
        paid_users = (await cursor.fetchone())[0]

        cursor = await self._conn.execute(
            "SELECT COUNT(*) FROM subscriptions WHERE expires_at > ?",
            (datetime.now().isoformat(),)
        )
        active_subs = (await cursor.fetchone())[0]

        return {
            "total_users": total_users,
            "trial_users": trial_users,
            "paid_users": paid_users,
            "active_subs": active_subs,
        }

    async def get_expired_unnotified_subscriptions(self) -> list:
        """Get expired subscriptions that haven't been notified yet."""
        cursor = await self._conn.execute(
            """SELECT s.id, s.user_id, u.telegram_id, s.telegram_payment_id
               FROM subscriptions s
               JOIN users u ON s.user_id = u.id
               WHERE s.expires_at < ? AND (s.notified = 0 OR s.notified IS NULL)""",
            (datetime.now().isoformat(),)
        )
        rows = await cursor.fetchall()
        return [{"id": r[0], "user_id": r[1], "telegram_id": r[2], "is_trial": r[3] == "TRIAL"} for r in rows]

    async def mark_subscription_notified(self, subscription_id: int):
        """Mark subscription as notified."""
        await self._conn.execute(
            "UPDATE subscriptions SET notified = 1 WHERE id = ?",
            (subscription_id,)
        )
        await self._conn.commit()


# Global database instance
db = Database()
