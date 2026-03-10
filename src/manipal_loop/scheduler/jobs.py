"""APScheduler-based job definitions for Manipal Local Loop."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore

from manipal_loop.config import config

logger = logging.getLogger(__name__)


class SchedulerManager:
    """Manages all scheduled background jobs using APScheduler."""

    def __init__(self) -> None:
        """Initialise the AsyncIOScheduler."""
        self._scheduler = AsyncIOScheduler(timezone=config.TIMEZONE)

    # ------------------------------------------------------------------

    def start(self, bot_app, db_manager, summarizer) -> None:
        """Register all jobs and start the scheduler.

        Args:
            bot_app: python-telegram-bot Application instance (may be None).
            db_manager: DatabaseManager instance.
            summarizer: GeminiSummarizer instance.
        """
        bot = bot_app.bot if bot_app else None

        # Job 1: Scrape every N minutes
        self._scheduler.add_job(
            _scrape_and_store,
            trigger=IntervalTrigger(minutes=config.SCRAPE_INTERVAL_MINUTES),
            args=[db_manager],
            id="scrape_job",
            replace_existing=True,
            misfire_grace_time=60,
        )

        # Job 2: Push high-urgency notifications (5 min after scrape window)
        self._scheduler.add_job(
            _push_notifications,
            trigger=IntervalTrigger(
                minutes=config.SCRAPE_INTERVAL_MINUTES,
            ),
            args=[bot, db_manager],
            id="notify_job",
            replace_existing=True,
            misfire_grace_time=60,
        )

        # Job 3: Daily digest at DIGEST_HOUR:DIGEST_MINUTE
        self._scheduler.add_job(
            _send_digest,
            trigger=CronTrigger(
                hour=config.DIGEST_HOUR,
                minute=config.DIGEST_MINUTE,
                timezone=config.TIMEZONE,
            ),
            args=[bot, db_manager, summarizer],
            id="digest_job",
            replace_existing=True,
        )

        # Job 4: Cleanup old updates at 11 PM IST
        self._scheduler.add_job(
            _cleanup,
            trigger=CronTrigger(hour=23, minute=0, timezone=config.TIMEZONE),
            args=[db_manager],
            id="cleanup_job",
            replace_existing=True,
        )

        self._scheduler.start()
        logger.info("Scheduler started with %d jobs", len(self._scheduler.get_jobs()))

    def shutdown(self) -> None:
        """Gracefully stop the scheduler."""
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped")


# ------------------------------------------------------------------
# Job functions
# ------------------------------------------------------------------

async def _scrape_and_store(db_manager) -> None:
    """Run all scrapers, classify/score items, and persist to DB."""
    from manipal_loop.processing.classifier import classify
    from manipal_loop.processing.dedup import is_duplicate
    from manipal_loop.processing.urgency import score_urgency
    from manipal_loop.scrapers import (
        GoogleNewsScraper,
        MAHENoticesScraper,
        PowerCutsScraper,
        RedditScraper,
        TwitterScraper,
        WeatherScraper,
    )

    scrapers = [
        GoogleNewsScraper(),
        MAHENoticesScraper(),
        RedditScraper(),
        TwitterScraper(),
        PowerCutsScraper(),
        WeatherScraper(),
    ]

    total_new = 0
    for scraper in scrapers:
        try:
            items = scraper.fetch()
        except Exception as exc:
            logger.error("%s.fetch() failed: %s", type(scraper).__name__, exc)
            continue

        for item in items:
            if is_duplicate(item.get("content_hash", ""), db_manager):
                continue

            item["category"] = classify(
                item.get("title", ""), item.get("body_text", "")
            )
            item["urgency_score"] = score_urgency(
                item.get("title", ""),
                item.get("body_text", ""),
                item.get("category", "General"),
            )

            db_manager.insert_update(item)
            total_new += 1

    logger.info("Scrape cycle complete — %d new items stored", total_new)


async def _push_notifications(bot, db_manager) -> None:
    """Send push notifications for unsent high-urgency updates."""
    if bot is None:
        return

    from manipal_loop.bot.notifications import send_push_notification

    updates = db_manager.get_unsent_updates()
    high_urgency = [u for u in updates if u.get("urgency_score", 1) >= 4]

    for update_data in high_urgency:
        await send_push_notification(bot, update_data, db_manager)


async def _send_digest(bot, db_manager, summarizer) -> None:
    """Send the daily digest to all subscribers."""
    if bot is None:
        return

    from manipal_loop.bot.notifications import send_daily_digest

    await send_daily_digest(bot, db_manager, summarizer)


async def _cleanup(db_manager) -> None:
    """Remove updates older than 7 days."""
    db_manager.cleanup_old_updates(days=7)
