"""Reddit scraper for r/manipal and r/udupi subreddits."""

import logging
from datetime import datetime, timezone
from typing import List

from manipal_loop.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

_URL = "https://www.reddit.com/r/manipal+udupi/new.json?limit=20"
_HEADERS = {"User-Agent": "ManipalLocalLoop/2.0"}


class RedditScraper(BaseScraper):
    """Fetches new posts from r/manipal and r/udupi via the public JSON API."""

    def fetch(self) -> List[dict]:
        """Retrieve the 20 newest posts, skipping stickied entries.

        Returns:
            List of standardised item dicts with category 'Campus Chatter'.
        """
        logger.info("Fetching Reddit posts from %s", _URL)
        response = self._make_request(_URL, headers=_HEADERS)

        if response is None:
            return []

        if response.status_code == 429:
            logger.warning("Reddit rate limit hit (429)")
            return []

        try:
            data = response.json()
        except Exception as exc:
            logger.error("Failed to parse Reddit JSON: %s", exc)
            return []

        posts = data.get("data", {}).get("children", [])
        items: List[dict] = []

        for post in posts:
            pd = post.get("data", {})

            if pd.get("stickied", False):
                continue

            title: str = pd.get("title", "").strip()
            body: str = pd.get("selftext", "").strip()
            permalink: str = pd.get("permalink", "")
            full_url = f"https://www.reddit.com{permalink}"

            created_utc: float = pd.get("created_utc", 0)
            timestamp = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

            # Best-effort thumbnail / preview image
            image_url = ""
            preview = pd.get("preview", {})
            preview_images = preview.get("images", [])
            if preview_images:
                image_url = preview_images[0].get("source", {}).get("url", "")
            elif pd.get("thumbnail", "").startswith("http"):
                image_url = pd["thumbnail"]

            subreddit = pd.get("subreddit", "reddit")
            items.append(
                self._build_item(
                    title=title,
                    body_text=body or title,
                    url=full_url,
                    source=f"r/{subreddit}",
                    category="Campus Chatter",
                    image_url=image_url,
                    timestamp=timestamp,
                )
            )

        logger.info("RedditScraper fetched %d items", len(items))
        return items
