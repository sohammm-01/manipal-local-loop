"""Push notification and daily digest delivery functions."""

import asyncio
import logging
from typing import List

logger = logging.getLogger(__name__)

_RATE_LIMIT_DELAY = 0.05  # seconds between Telegram sends


async def send_push_notification(bot, update_data: dict, db_manager) -> None:
    """Send a push notification to all relevant subscribers.

    Respects per-message rate limits to avoid Telegram flood errors.

    Args:
        bot: A python-telegram-bot Bot instance.
        update_data: Standardised update dict including 'id' and 'category'.
        db_manager: DatabaseManager instance.
    """
    category = update_data.get("category", "General")
    update_id = update_data.get("id")
    title = update_data.get("title", "")
    url = update_data.get("url", "")
    urgency = update_data.get("urgency_score", 1)

    subscribers: List[dict] = db_manager.get_subscribers(category)
    if not subscribers:
        logger.debug("No subscribers for category '%s'", category)
        return

    urgency_emoji = "🚨" if urgency >= 5 else "⚠️" if urgency >= 4 else "📢"
    link_part = f'\n🔗 <a href="{url}">Read more</a>' if url else ""
    message = (
        f"{urgency_emoji} <b>[{category}]</b> {title}{link_part}"
    )

    for user in subscribers:
        try:
            await bot.send_message(
                chat_id=user["telegram_chat_id"],
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            if update_id is not None:
                db_manager.mark_sent(update_id, user["id"])
            await asyncio.sleep(_RATE_LIMIT_DELAY)
        except Exception as exc:
            logger.warning(
                "Failed to send notification to chat_id=%s: %s",
                user.get("telegram_chat_id"),
                exc,
            )


async def send_daily_digest(bot, db_manager, summarizer) -> None:
    """Send the daily digest to all active subscribers.

    Args:
        bot: A python-telegram-bot Bot instance.
        db_manager: DatabaseManager instance.
        summarizer: GeminiSummarizer (or compatible) instance.
    """
    updates = db_manager.get_todays_updates()
    digest = summarizer.generate_daily_digest(updates)

    try:
        conn = db_manager._get_conn()
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active = 1"
        ).fetchall()
        subscribers = [dict(r) for r in rows]
    except Exception as exc:
        logger.error("Could not fetch all active subscribers: %s", exc)
        return

    logger.info("Sending daily digest to %d subscribers", len(subscribers))
    for user in subscribers:
        try:
            await bot.send_message(
                chat_id=user["telegram_chat_id"],
                text=digest,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
            await asyncio.sleep(_RATE_LIMIT_DELAY)
        except Exception as exc:
            logger.warning(
                "Failed to send digest to chat_id=%s: %s",
                user.get("telegram_chat_id"),
                exc,
            )
