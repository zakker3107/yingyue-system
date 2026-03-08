from __future__ import annotations

import sqlite3
from contextlib import contextmanager

from services.core.settings import DB_PATH


def initialize_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA temp_store=MEMORY;
            PRAGMA cache_size=-20000;
            PRAGMA foreign_keys=ON;

            CREATE TABLE IF NOT EXISTS news_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                link TEXT,
                source TEXT NOT NULL,
                topic TEXT NOT NULL,
                published_at TEXT,
                summary TEXT,
                inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS philosophy_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT,
                school TEXT,
                era TEXT,
                summary TEXT NOT NULL,
                keywords TEXT,
                inserted_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS trend_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                bucket TEXT NOT NULL,
                captured_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS observation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                observed_date TEXT NOT NULL UNIQUE,
                sentiment_score REAL NOT NULL,
                sentiment_label TEXT NOT NULL,
                top_topic TEXT NOT NULL,
                second_topic TEXT NOT NULL,
                key_takeaway TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS network_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                source TEXT NOT NULL,
                source_url TEXT,
                description TEXT,
                event_date TEXT,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'active',
                related_topics TEXT,
                tags TEXT,
                source_news_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(source_news_id) REFERENCES news_items(id)
            );

            CREATE INDEX IF NOT EXISTS idx_news_published_at
            ON news_items(published_at DESC);

            CREATE INDEX IF NOT EXISTS idx_news_topic
            ON news_items(topic);

            CREATE INDEX IF NOT EXISTS idx_philosophy_author
            ON philosophy_entries(author);

            CREATE INDEX IF NOT EXISTS idx_trends_metric
            ON trend_snapshots(metric_value DESC);

            CREATE INDEX IF NOT EXISTS idx_observation_date
            ON observation_logs(observed_at DESC);

            CREATE INDEX IF NOT EXISTS idx_network_event_type
            ON network_events(event_type);

            CREATE INDEX IF NOT EXISTS idx_network_event_date
            ON network_events(event_date DESC);

            CREATE INDEX IF NOT EXISTS idx_network_event_status
            ON network_events(status);

            CREATE INDEX IF NOT EXISTS idx_network_event_severity
            ON network_events(severity);
            """
        )


@contextmanager
def db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
