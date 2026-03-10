"""Telegram bot entry point — wires up Application and command handlers."""

import logging

from manipal_loop.config import config

logger = logging.getLogger(__name__)


def start_bot():
    """Build and return the Telegram Application.

    Returns:
        A configured ``telegram.ext.Application`` instance, or None if
        ``TELEGRAM_BOT_TOKEN`` is not set.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not set; Telegram bot disabled")
        return None

    try:
        from telegram.ext import Application, CommandHandler

        from manipal_loop.bot.commands import (
            alerts_command,
            campus_command,
            digest_command,
            events_command,
            help_command,
            mystatus_command,
            news_command,
            powercut_command,
            report_command,
            start_command,
            subscribe_command,
            traffic_command,
            unsubscribe_command,
            weather_command,
        )

        app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("powercut", powercut_command))
        app.add_handler(CommandHandler("weather", weather_command))
        app.add_handler(CommandHandler("events", events_command))
        app.add_handler(CommandHandler("news", news_command))
        app.add_handler(CommandHandler("traffic", traffic_command))
        app.add_handler(CommandHandler("campus", campus_command))
        app.add_handler(CommandHandler("alerts", alerts_command))
        app.add_handler(CommandHandler("digest", digest_command))
        app.add_handler(CommandHandler("subscribe", subscribe_command))
        app.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
        app.add_handler(CommandHandler("mystatus", mystatus_command))
        app.add_handler(CommandHandler("report", report_command))

        logger.info("Telegram bot application configured")
        return app

    except Exception as exc:
        logger.error("Failed to configure Telegram bot: %s", exc)
        return None
