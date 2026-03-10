"""Configuration module — loads all settings from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration loaded from environment variables."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # AI / APIs
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")

    # Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/manipal_loop.db")

    # Scheduling
    SCRAPE_INTERVAL_MINUTES: int = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "30"))
    DIGEST_HOUR: int = int(os.getenv("DIGEST_HOUR", "8"))
    DIGEST_MINUTE: int = int(os.getenv("DIGEST_MINUTE", "0"))
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # HTTP
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))


config = Config()
