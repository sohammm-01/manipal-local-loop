"""Gemini-powered text summariser for single updates and daily digests."""

import logging
from typing import List

from manipal_loop.config import config

logger = logging.getLogger(__name__)


class GeminiSummarizer:
    """Uses Google Gemini Pro to summarise news updates and produce daily digests."""

    def __init__(self) -> None:
        """Initialise the Gemini client if an API key is available."""
        self._model = None

        if not config.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set; summarisation disabled")
            return

        try:
            import google.generativeai as genai  # type: ignore

            genai.configure(api_key=config.GEMINI_API_KEY)
            self._model = genai.GenerativeModel("gemini-pro")
            logger.info("Gemini summariser initialised")
        except Exception as exc:
            logger.error("Failed to initialise Gemini: %s", exc)

    # ------------------------------------------------------------------

    def summarize_single(self, update: dict) -> str:
        """Generate a two-sentence summary of a single update.

        Falls back to the item's title if Gemini is unavailable or errors.

        Args:
            update: A standardised update dict with 'title' and 'body_text'.

        Returns:
            Two-sentence summary string.
        """
        title = update.get("title", "")
        body = update.get("body_text", "")

        if self._model is None:
            return title

        prompt = (
            f"Summarise the following news item from Manipal/Udupi in exactly "
            f"two concise sentences suitable for a Telegram notification:\n\n"
            f"Title: {title}\nBody: {body}"
        )

        try:
            response = self._model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini summarize_single error: %s", exc)
            return title

    def generate_daily_digest(self, updates: List[dict]) -> str:
        """Produce a morning briefing digest from a list of today's updates.

        Args:
            updates: List of update dicts for the current day.

        Returns:
            Formatted digest string.
        """
        if not updates:
            return "No significant updates in the last 24 hours. Stay tuned! 🙂"

        if self._model is None:
            return self._fallback_digest(updates)

        bullet_points = "\n".join(
            f"- [{u.get('category', 'General')}] {u.get('title', '')}"
            for u in updates[:20]
        )

        prompt = (
            "You are a hyperlocal news assistant for Manipal, India. "
            "Based on the following news items from the past 24 hours, "
            "write a friendly morning briefing (3-5 sentences) for Telegram. "
            "Highlight the most important items and use an upbeat tone.\n\n"
            f"{bullet_points}"
        )

        try:
            response = self._model.generate_content(prompt)
            return response.text.strip()
        except Exception as exc:
            logger.error("Gemini generate_daily_digest error: %s", exc)
            return self._fallback_digest(updates)

    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_digest(updates: List[dict]) -> str:
        """Build a plain-text digest without Gemini.

        Args:
            updates: List of update dicts.

        Returns:
            Formatted plain-text digest.
        """
        lines = ["📰 <b>Daily Digest — Manipal Local Loop</b>\n"]
        for u in updates[:10]:
            cat = u.get("category", "General")
            title = u.get("title", "")
            lines.append(f"• [{cat}] {title}")
        return "\n".join(lines)
