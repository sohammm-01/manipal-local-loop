"""MAHE (Manipal Academy of Higher Education) notices scraper."""

import logging
from typing import List

from bs4 import BeautifulSoup

from manipal_loop.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_URL = "https://manipal.edu/mu.html"
_KEYWORDS = ["notice", "update", "circular", "announcement"]
_MAX_ITEMS = 10
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36 ManipalLocalLoop/2.0"
    )
}


class MAHENoticesScraper(BaseScraper):
    """Scrapes official notices from the Manipal University website."""

    def fetch(self) -> List[dict]:
        """Fetch official notices from manipal.edu.

        Returns:
            List of item dicts (up to 10 most recent notices).
        """
        logger.info("Fetching MAHE notices from %s", _URL)
        response = self._make_request(_URL, headers=_HEADERS)
        if response is None:
            logger.warning("Could not reach MAHE website")
            return []

        try:
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as exc:
            logger.error("BeautifulSoup parse error: %s", exc)
            return []

        items: List[dict] = []
        seen_hrefs: set = set()

        for tag in soup.find_all("a", href=True):
            text: str = tag.get_text(strip=True)
            href: str = tag["href"]

            if not any(kw in text.lower() for kw in _KEYWORDS):
                continue
            if href in seen_hrefs:
                continue

            seen_hrefs.add(href)

            # Resolve relative URLs
            if href.startswith("/"):
                href = f"https://manipal.edu{href}"
            elif not href.startswith("http"):
                href = f"https://manipal.edu/{href}"

            items.append(
                self._build_item(
                    title=text,
                    body_text=text,
                    url=href,
                    source="MAHE",
                    category="Official Alert",
                    raw_language="en",
                )
            )

            if len(items) >= _MAX_ITEMS:
                break

        logger.info("MAHENoticesScraper fetched %d items", len(items))
        return items
