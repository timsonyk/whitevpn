from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Telegram Bot
    bot_token: str

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    base_url: str = "https://SERVER_IP"

    # Subscription
    subscription_price_stars: int = 189
    subscription_days: int = 30

    # GitHub config URL
    config_url: str = "https://raw.githubusercontent.com/igareck/vpn-configs-for-russia/main/Vless-Reality-White-Lists-Rus-Mobile.txt"

    # Database
    database_path: str = "./data/whitevpn.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
