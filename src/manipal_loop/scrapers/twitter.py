"""Twitter / X scraper via Nitter RSS fallback instances."""

import logging
from typing import List

import feedparser

from manipal_loop.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_NITTER_INSTANCES = [
    "https://nitter.poast.org",
    "https://nitter.privacydev.net",
    "https://nitter.net",
]
_HANDLES = ["DCUdupi", "udupipolice", "manipaluniv"]
_TWEETS_PER_HANDLE = 5


class TwitterScraper(BaseScraper):
    """Scrapes tweets via Nitter RSS with automatic instance fallback."""

    def fetch(self) -> List[dict]:
        """Fetch top-5 tweets from each tracked account.

        Returns:
            List of standardised item dicts with category 'City News'.
        """
        items: List[dict] = []

        for handle in _HANDLES:
            tweets = self._fetch_handle(handle)
            items.extend(tweets)

        logger.info("TwitterScraper fetched %d items total", len(items))
        return items

    def _fetch_handle(self, handle: str) -> List[dict]:
        """Try each Nitter instance until one succeeds for the given handle.

        Args:
            handle: Twitter/X username without '@'.

        Returns:
            List of tweet item dicts (up to _TWEETS_PER_HANDLE).
        """
        for instance in _NITTER_INSTANCES:
            rss_url = f"{instance}/{handle}/rss"
            try:
                feed = feedparser.parse(rss_url)
                if feed.bozo and not feed.entries:
                    continue

                tweets: List[dict] = []
                for entry in feed.entries[:_TWEETS_PER_HANDLE]:
                    title = entry.get("title", "").strip()
                    link = entry.get("link", "")
                    published = entry.get("published", "")

                    item = self._build_item(
                        title=title,
                        body_text=entry.get("summary", title),
                        url=link,
                        source=f"@{handle}",
                        category="City News",
                        timestamp=published or None,
                    )
                    tweets.append(item)

                if tweets:
                    logger.info(
                        "TwitterScraper: got %d tweets for @%s via %s",
                        len(tweets),
                        handle,
                        instance,
                    )
                    return tweets

            except Exception as exc:
                logger.warning(
                    "Nitter instance %s failed for @%s: %s", instance, handle, exc
                )

        logger.warning("All Nitter instances failed for @%s", handle)
        return []
