from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from services.core.storage import db_connection

TOPIC_KEYWORDS = {
    "ai": ["ai", "artificial intelligence", "model", "agent"],
    "chip": ["chip", "semiconductor", "gpu", "accelerator"],
    "policy": ["policy", "regulation", "law", "governance"],
    "security": ["security", "cyber", "vulnerability", "attack"],
    "economy": ["market", "economy", "inflation", "trade"],
}


def _score_topics(text: str) -> list[str]:
    lower = text.lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(word in lower for word in keywords):
            matched.append(topic)
    if not matched:
        matched.append("general")
    return matched


def build_trend_snapshot() -> dict[str, float]:
    with db_connection() as conn:
        rows = conn.execute(
            "SELECT title, summary FROM news_items ORDER BY id DESC LIMIT 500"
        ).fetchall()

        counter: Counter[str] = Counter()
        for row in rows:
            text = f"{row['title']} {row['summary']}"
            counter.update(_score_topics(text))

        total = sum(counter.values()) or 1
        pct_map = {k: round(v * 100.0 / total, 2) for k, v in counter.items()}

        captured_at = datetime.now(timezone.utc).isoformat()
        conn.execute("DELETE FROM trend_snapshots")
        conn.executemany(
            """
            INSERT INTO trend_snapshots(metric_name, metric_value, bucket, captured_at)
            VALUES(?, ?, ?, ?)
            """,
            [("topic_share", value, key, captured_at) for key, value in pct_map.items()],
        )
        conn.commit()

    return pct_map
