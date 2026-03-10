"""Manipal Local Loop — main entry point."""

import asyncio
import logging
import signal
import sys
from typing import Any

from manipal_loop.config import config
from manipal_loop.database.db import get_db
from manipal_loop.scheduler.jobs import SchedulerManager
from manipal_loop.summarizer.gemini import GeminiSummarizer

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Initialise all components and run the bot until interrupted."""
    logger.info("🚀 Starting Manipal Local Loop v2.0.0")

    # Database
    db = get_db()
    db.init_db()

    # Summariser
    summarizer = GeminiSummarizer()

    # Telegram bot application
    from manipal_loop.bot.telegram_bot import start_bot
    bot_app = start_bot()

    # Scheduler
    scheduler = SchedulerManager()
    scheduler.start(bot_app, db, summarizer)

    # Graceful shutdown hooks
    loop = asyncio.get_running_loop()

    def _shutdown(signum: int, frame: Any) -> None:
        logger.info("Received signal %s — shutting down", signum)
        scheduler.shutdown()
        if bot_app:
            loop.create_task(bot_app.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    if bot_app:
        logger.info("Starting Telegram bot polling…")
        async with bot_app:
            await bot_app.initialize()
            await bot_app.start()
            await bot_app.updater.start_polling()

            # Keep running until interrupted
            stop_event = asyncio.Event()
            await stop_event.wait()
    else:
        logger.warning("Telegram bot not configured — running scheduler only")
        stop_event = asyncio.Event()
        await stop_event.wait()


if __name__ == "__main__":
    asyncio.run(main())
