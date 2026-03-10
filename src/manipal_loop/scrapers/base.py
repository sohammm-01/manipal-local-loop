"""Abstract base class for all scrapers with retry, rate-limiting, and logging."""

import hashlib
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests

from manipal_loop.config import config

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base scraper with built-in retry logic, rate limiting, and standardised output."""

    def __init__(self, rate_limit_delay: float = 1.0) -> None:
        """Initialise the scraper.

        Args:
            rate_limit_delay: Seconds to wait between successive HTTP requests.
        """
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch(self) -> List[dict]:
        """Fetch items from the source.

        Returns:
            A list of standardised item dicts (see _build_item).
        """

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _make_request(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[dict] = None,
    ) -> Optional[requests.Response]:
        """Make an HTTP GET request with retry + exponential back-off.

        Args:
            url: Target URL.
            headers: Optional extra request headers.
            params: Optional query parameters.

        Returns:
            Response object on success, None on permanent failure.
        """
        delays = [1, 2, 4]
        last_exc: Optional[Exception] = None

        for attempt, delay in enumerate(delays, start=1):
            self._rate_limit()
            try:
                resp = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=config.REQUEST_TIMEOUT,
                )
                resp.raise_for_status()
                return resp
            except requests.RequestException as exc:
                last_exc = exc
                logger.warning(
                    "Request attempt %d/%d failed for %s: %s",
                    attempt,
                    config.MAX_RETRIES,
                    url,
                    exc,
                )
                if attempt < len(delays):
                    time.sleep(delay)

        logger.error("All retries exhausted for %s: %s", url, last_exc)
        return None

    # ------------------------------------------------------------------
    # Item builder
    # ------------------------------------------------------------------

    def _build_item(
        self,
        title: str,
        body_text: str,
        url: str,
        source: str,
        category: str,
        image_url: str = "",
        raw_language: str = "en",
        timestamp: Optional[str] = None,
    ) -> dict:
        """Build a standardised scraper result dict.

        Args:
            title: Article/post headline.
            body_text: Body or summary text.
            url: Canonical link to the item.
            source: Human-readable source name.
            category: One of the defined content categories.
            image_url: Optional thumbnail URL.
            raw_language: BCP-47 language code detected at source.
            timestamp: ISO-formatted datetime string; defaults to now (UTC).

        Returns:
            Standardised item dict.
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        content_hash = self._generate_hash(title, source, timestamp[:10])

        return {
            "content_hash": content_hash,
            "timestamp": timestamp,
            "title": title,
            "body_text": body_text,
            "image_url": image_url,
            "source": source,
            "category": category,
            "url": url,
            "raw_language": raw_language,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Block until the minimum inter-request delay has elapsed."""
        elapsed = time.monotonic() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self._last_request_time = time.monotonic()

    @staticmethod
    def _generate_hash(title: str, source: str, date: str) -> str:
        """Return a SHA-256 hex digest from title + source + date."""
        raw = f"{title}{source}{date}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
