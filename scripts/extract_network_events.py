#!/usr/bin/env python
"""Extract network events from news items using keyword rules."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.core.storage import db_connection


NETWORK_EVENT_KEYWORDS = {
    "security": {
        "keywords": ["breach", "attack", "vulnerability", "exploit", "hack", "malware", "ransomware", "zero-day"],
        "severity": "high",
    },
    "infrastructure": {
        "keywords": ["outage", "downtime", "failure", "collapse", "crash", "dns", "ddos"],
        "severity": "high",
    },
    "policy": {
        "keywords": ["regulation", "ban", "restriction", "law", "fine", "compliance", "gdpr", "ccpa"],
        "severity": "medium",
    },
    "technology": {
        "keywords": ["protocol", "standard", "update", "release", "upgrade", "ipv6", "http3", "web3"],
        "severity": "low",
    },
    "acquisition": {
        "keywords": ["acquire", "acquisition", "merger", "buyout", "takeover", "investment"],
        "severity": "medium",
    },
    "incident": {
        "keywords": ["incident", "emergency", "crisis", "disaster", "accident"],
        "severity": "high",
    },
}


def classify_event(title: str, summary: str, topic: str) -> tuple[str, str] | None:
    text = (title + " " + (summary or "")).lower()
    for event_type, config in NETWORK_EVENT_KEYWORDS.items():
        for keyword in config["keywords"]:
            if keyword in text:
                return event_type, config["severity"]
    return None


def extract_events() -> int:
    extracted_count = 0

    with db_connection() as conn:
        news_items = conn.execute(
            """
            SELECT n.id, n.title, n.link, n.source, n.topic, n.published_at, n.summary
            FROM news_items n
            WHERE NOT EXISTS (
                SELECT 1
                FROM network_events e
                WHERE e.source_news_id = n.id
            )
            ORDER BY n.published_at DESC
            LIMIT 100
            """
        ).fetchall()

        existing_pairs = {
            (row[0], row[1])
            for row in conn.execute(
                "SELECT event_name, event_type FROM network_events"
            ).fetchall()
        }

        now = datetime.now().isoformat()
        to_insert: list[tuple[object, ...]] = []

        for news in news_items:
            classification = classify_event(news["title"], news["summary"], news["topic"])
            if not classification:
                continue

            event_type, severity = classification
            pair = (news["title"], event_type)
            if pair in existing_pairs:
                continue

            existing_pairs.add(pair)
            to_insert.append(
                (
                    news["title"],
                    event_type,
                    news["source"],
                    news["link"],
                    news["summary"],
                    news["published_at"],
                    severity,
                    "active",
                    news["topic"],
                    news["id"],
                    now,
                    now,
                )
            )

        if to_insert:
            conn.executemany(
                """
                INSERT INTO network_events
                (event_name, event_type, source, source_url, description, event_date,
                 severity, status, related_topics, source_news_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                to_insert,
            )
            conn.commit()
            extracted_count = len(to_insert)

    return extracted_count


def main() -> int:
    print("[Extract] extracting network events from recent news...")
    try:
        count = extract_events()
        print(f"[Done] extracted {count} event(s)")
        return 0
    except Exception as e:
        print(f"[Error] extraction failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
