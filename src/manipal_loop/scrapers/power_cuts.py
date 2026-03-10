"""Power cuts scraper — MESCOM website with Google News RSS fallback."""

import logging
from typing import List
from urllib.parse import quote

import feedparser
from bs4 import BeautifulSoup

from manipal_loop.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_MESCOM_URL = "https://mescom.karnataka.gov.in"
_FALLBACK_QUERY = "MESCOM power cut Manipal Udupi"
_FALLBACK_URL = (
    "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/120.0 Safari/537.36 ManipalLocalLoop/2.0"
    )
}


class PowerCutsScraper(BaseScraper):
    """Fetches scheduled power cut information for the Manipal / Udupi area."""

    def fetch(self) -> List[dict]:
        """Attempt MESCOM website; fall back to Google News RSS.

        Returns:
            List of standardised item dicts with category 'Power Cut'.
        """
        items = self._fetch_mescom()
        if not items:
            items = self._fetch_fallback()
        logger.info("PowerCutsScraper fetched %d items", len(items))
        return items

    # ------------------------------------------------------------------

    def _fetch_mescom(self) -> List[dict]:
        """Scrape MESCOM website for power-cut notices."""
        logger.info("Fetching power cuts from MESCOM: %s", _MESCOM_URL)
        response = self._make_request(_MESCOM_URL, headers=_HEADERS)
        if response is None:
            return []

        try:
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as exc:
            logger.error("MESCOM parse error: %s", exc)
            return []

        items: List[dict] = []
        for tag in soup.find_all(["a", "p", "li"]):
            text = tag.get_text(strip=True)
            lower = text.lower()
            if not any(kw in lower for kw in ["power cut", "shutdown", "interruption", "outage"]):
                continue
            if not any(loc in lower for loc in ["manipal", "udupi", "mangaluru", "kundapura"]):
                continue

            href = tag.get("href", _MESCOM_URL)
            if href.startswith("/"):
                href = f"{_MESCOM_URL}{href}"
            elif not href.startswith("http"):
                href = _MESCOM_URL

            items.append(
                self._build_item(
                    title=text[:200],
                    body_text=text,
                    url=href,
                    source="MESCOM",
                    category="Power Cut",
                )
            )
            if len(items) >= 10:
                break

        return items

    def _fetch_fallback(self) -> List[dict]:
        """Use Google News RSS as a fallback source for power-cut news."""
        logger.info("PowerCuts: using Google News RSS fallback")
        url = _FALLBACK_URL.format(query=quote(_FALLBACK_QUERY))
        try:
            feed = feedparser.parse(url)
        except Exception as exc:
            logger.error("feedparser error in PowerCuts fallback: %s", exc)
            return []

        items: List[dict] = []
        for entry in feed.entries[:10]:
            title = entry.get("title", "").strip()
            parts = title.rsplit(" - ", 1)
            source = parts[-1].strip() if len(parts) > 1 else "Google News"
            clean_title = parts[0].strip() if len(parts) > 1 else title

            items.append(
                self._build_item(
                    title=clean_title,
                    body_text=entry.get("summary", clean_title),
                    url=entry.get("link", ""),
                    source=source,
                    category="Power Cut",
                    timestamp=entry.get("published") or None,
                )
            )
        return items
