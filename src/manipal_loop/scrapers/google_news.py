"""Google News RSS scraper for Manipal / Udupi / Mangaluru news."""

import logging
from typing import List
from urllib.parse import quote

import feedparser

from manipal_loop.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_QUERY = "(Manipal OR Udupi OR Mangaluru) when:24h"
_RSS_BASE = (
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)
_MAX_ITEMS = 20


class GoogleNewsScraper(BaseScraper):
    """Fetches recent local news from Google News RSS feed."""

    def fetch(self) -> List[dict]:
        """Parse Google News RSS and return up to 20 standardised items.

        Returns:
            List of item dicts matching the BaseScraper schema.
        """
        url = _RSS_BASE.format(query=quote(_QUERY))
        logger.info("Fetching Google News RSS: %s", url)

        try:
            feed = feedparser.parse(url)
        except Exception as exc:  # feedparser rarely raises but be safe
            logger.error("feedparser error: %s", exc)
            return []

        items: List[dict] = []
        for entry in feed.entries[:_MAX_ITEMS]:
            title: str = entry.get("title", "").strip()
            link: str = entry.get("link", "")

            # Source is appended after " - " in the title by Google News
            parts = title.rsplit(" - ", 1)
            source = parts[-1].strip() if len(parts) > 1 else "Google News"
            clean_title = parts[0].strip() if len(parts) > 1 else title

            published = entry.get("published", "")

            item = self._build_item(
                title=clean_title,
                body_text=entry.get("summary", clean_title),
                url=link,
                source=source,
                category="City News",
                raw_language="en",
                timestamp=published or None,
            )
            items.append(item)

        logger.info("GoogleNewsScraper fetched %d items", len(items))
        return items
