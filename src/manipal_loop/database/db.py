"""Database access layer using sqlite3."""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from manipal_loop.database.models import ALL_TABLES

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages all SQLite interactions for Manipal Local Loop."""

    def __init__(self, db_path: str) -> None:
        """Open (or create) the SQLite database at *db_path*.

        Args:
            db_path: Filesystem path to the .db file.
        """
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        """Return the shared connection, creating it if necessary."""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL;")
        return self._conn

    def init_db(self) -> None:
        """Create all tables if they do not already exist."""
        conn = self._get_conn()
        for ddl in ALL_TABLES:
            conn.execute(ddl)
        conn.commit()
        logger.info("Database initialised at %s", self.db_path)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Update operations
    # ------------------------------------------------------------------

    def insert_update(self, data: dict) -> Optional[int]:
        """Insert a new update record.

        Args:
            data: Dict with keys matching the 'updates' table columns.

        Returns:
            The new row id, or None if the content_hash already exists.
        """
        sql = """
        INSERT INTO updates
            (content_hash, timestamp, title, body_text, image_url, source,
             category, url, language, urgency_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            conn = self._get_conn()
            cur = conn.execute(
                sql,
                (
                    data.get("content_hash", ""),
                    data.get("timestamp", ""),
                    data.get("title", ""),
                    data.get("body_text", ""),
                    data.get("image_url", ""),
                    data.get("source", ""),
                    data.get("category", "General"),
                    data.get("url", ""),
                    data.get("raw_language", "en"),
                    data.get("urgency_score", 1),
                ),
            )
            conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            logger.debug("Duplicate content_hash: %s", data.get("content_hash"))
            return None
        except sqlite3.Error as exc:
            logger.error("insert_update error: %s", exc)
            return None

    def update_exists(self, content_hash: str) -> bool:
        """Check whether a content_hash is already in the database.

        Args:
            content_hash: SHA-256 hex string.

        Returns:
            True if the hash already exists, False otherwise.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM updates WHERE content_hash = ?", (content_hash,)
        ).fetchone()
        return row is not None

    def get_unsent_updates(self, category: Optional[str] = None) -> List[dict]:
        """Return updates that have not been sent to any user yet.

        Args:
            category: Optional category filter.

        Returns:
            List of update dicts.
        """
        conn = self._get_conn()
        if category:
            rows = conn.execute(
                """
                SELECT * FROM updates
                WHERE id NOT IN (SELECT update_id FROM sent_alerts)
                  AND category = ?
                ORDER BY urgency_score DESC, timestamp DESC
                """,
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT * FROM updates
                WHERE id NOT IN (SELECT update_id FROM sent_alerts)
                ORDER BY urgency_score DESC, timestamp DESC
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def get_todays_updates(self) -> List[dict]:
        """Return all updates created today (UTC).

        Returns:
            List of update dicts ordered by urgency then timestamp.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT * FROM updates
            WHERE DATE(created_at) = ?
            ORDER BY urgency_score DESC, timestamp DESC
            """,
            (today,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_recent_updates(self, hours: int = 24) -> List[dict]:
        """Return updates from the last *hours* hours.

        Args:
            hours: Look-back window in hours.

        Returns:
            List of update dicts.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT * FROM updates
            WHERE timestamp >= ?
            ORDER BY urgency_score DESC, timestamp DESC
            """,
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def cleanup_old_updates(self, days: int = 7) -> None:
        """Delete updates older than *days* days.

        Args:
            days: Retention period in days.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        conn = self._get_conn()
        conn.execute("DELETE FROM updates WHERE timestamp < ?", (cutoff,))
        conn.commit()
        logger.info("Cleaned up updates older than %d days", days)

    # ------------------------------------------------------------------
    # User operations
    # ------------------------------------------------------------------

    def add_user(self, chat_id: int, username: str = "") -> int:
        """Insert or ignore a Telegram user.

        Args:
            chat_id: Telegram chat ID.
            username: Optional Telegram username.

        Returns:
            The user's row id (existing or new).
        """
        conn = self._get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_chat_id, username) VALUES (?, ?)",
            (chat_id, username),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id FROM users WHERE telegram_chat_id = ?", (chat_id,)
        ).fetchone()
        return row["id"] if row else -1

    def update_subscriptions(self, chat_id: int, categories: List[str]) -> None:
        """Overwrite the subscribed categories for a user.

        Args:
            chat_id: Telegram chat ID.
            categories: List of category strings.
        """
        conn = self._get_conn()
        conn.execute(
            "UPDATE users SET subscribed_categories = ? WHERE telegram_chat_id = ?",
            (json.dumps(categories), chat_id),
        )
        conn.commit()

    def get_subscribers(self, category: str) -> List[dict]:
        """Return all active subscribers for a given category.

        Args:
            category: Category string to filter on.

        Returns:
            List of user dicts.
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active = 1"
        ).fetchall()
        subscribers: List[dict] = []
        for row in rows:
            cats = json.loads(row["subscribed_categories"] or "[]")
            if not cats or category in cats:
                subscribers.append(dict(row))
        return subscribers

    def mark_sent(self, update_id: int, user_id: int) -> None:
        """Record that an update was sent to a user.

        Args:
            update_id: PK of the update row.
            user_id: PK of the user row.
        """
        conn = self._get_conn()
        conn.execute(
            "INSERT OR IGNORE INTO sent_alerts (update_id, user_id) VALUES (?, ?)",
            (update_id, user_id),
        )
        conn.commit()

    def get_user_subscriptions(self, chat_id: int) -> List[str]:
        """Return the list of subscribed categories for a Telegram user.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            List of category strings, or empty list if user not found.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT subscribed_categories FROM users WHERE telegram_chat_id = ?",
            (chat_id,),
        ).fetchone()
        if not row:
            return []
        return json.loads(row["subscribed_categories"] or "[]")

    def get_user_row(self, chat_id: int) -> Optional[dict]:
        """Return the full user row for a given Telegram chat ID.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            User dict, or None if not found.
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_chat_id = ?", (chat_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_active_users(self) -> List[dict]:
        """Return all active users.

        Returns:
            List of user dicts for is_active = 1.
        """
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM users WHERE is_active = 1"
        ).fetchall()
        return [dict(r) for r in rows]


# Module-level singleton
_db_instance: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Return the module-level DatabaseManager singleton.

    Returns:
        Shared DatabaseManager instance.
    """
    global _db_instance
    if _db_instance is None:
        from manipal_loop.config import config
        _db_instance = DatabaseManager(config.DATABASE_PATH)
        _db_instance.init_db()
    return _db_instance


db = get_db()
