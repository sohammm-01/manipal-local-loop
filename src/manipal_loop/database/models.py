"""SQLite schema definitions for Manipal Local Loop."""

UPDATES_TABLE = """
CREATE TABLE IF NOT EXISTS updates (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash  TEXT    NOT NULL UNIQUE,
    timestamp     TEXT    NOT NULL,
    title         TEXT    NOT NULL,
    body_text     TEXT    DEFAULT '',
    image_url     TEXT    DEFAULT '',
    source        TEXT    DEFAULT '',
    category      TEXT    DEFAULT 'General',
    url           TEXT    DEFAULT '',
    language      TEXT    DEFAULT 'en',
    is_translated INTEGER DEFAULT 0,
    summary       TEXT    DEFAULT '',
    urgency_score INTEGER DEFAULT 1,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_chat_id     INTEGER NOT NULL UNIQUE,
    username             TEXT    DEFAULT '',
    subscribed_categories TEXT   DEFAULT '[]',
    created_at           TEXT    NOT NULL DEFAULT (datetime('now')),
    is_active            INTEGER DEFAULT 1
);
"""

SENT_ALERTS_TABLE = """
CREATE TABLE IF NOT EXISTS sent_alerts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    update_id  INTEGER NOT NULL REFERENCES updates(id),
    user_id    INTEGER NOT NULL REFERENCES users(id),
    sent_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

ALL_TABLES = [UPDATES_TABLE, USERS_TABLE, SENT_ALERTS_TABLE]
