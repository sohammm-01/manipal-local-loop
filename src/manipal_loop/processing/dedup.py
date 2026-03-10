"""Deduplication utilities — content-hash generation and lookup."""

import hashlib
import logging

logger = logging.getLogger(__name__)


def generate_content_hash(title: str, source: str, date: str) -> str:
    """Generate a deterministic SHA-256 hash from title, source, and date.

    Args:
        title: Item headline.
        source: Publisher / origin string.
        date: Date string (e.g. YYYY-MM-DD).

    Returns:
        64-character lowercase hex digest.
    """
    raw = f"{title}{source}{date}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def is_duplicate(content_hash: str, db_manager) -> bool:
    """Check whether *content_hash* is already stored in the database.

    Args:
        content_hash: SHA-256 hex string to look up.
        db_manager: A DatabaseManager instance with an ``update_exists`` method.

    Returns:
        True if the hash exists, False otherwise.
    """
    try:
        return db_manager.update_exists(content_hash)
    except Exception as exc:
        logger.error("Dedup check failed: %s", exc)
        return False
