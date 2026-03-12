from __future__ import annotations

import json

from services.core.settings import PHILOSOPHY_SEED
from services.core.storage import db_connection


def load_seed_entries() -> list[dict[str, str]]:
    with PHILOSOPHY_SEED.open("r", encoding="utf-8-sig") as f:
        raw = json.load(f)

    normalized = []
    for item in raw:
        normalized.append(
            {
                "title": item.get("title", "Untitled"),
                "author": item.get("author", "Unknown"),
                "school": item.get("school", "Unknown"),
                "era": item.get("era", "Unknown"),
                "summary": item.get("summary", ""),
                "keywords": ",".join(item.get("keywords", [])),
            }
        )
    return normalized


def store_philosophy_entries(entries: list[dict[str, str]]) -> int:
    with db_connection() as conn:
        conn.execute("DELETE FROM philosophy_entries")
        conn.executemany(
            """
            INSERT INTO philosophy_entries(title, author, school, era, summary, keywords)
            VALUES(:title, :author, :school, :era, :summary, :keywords)
            """,
            entries,
        )
        conn.commit()
    return len(entries)


def run_philosophy_kb_refresh() -> int:
    entries = load_seed_entries()
    return store_philosophy_entries(entries)


def ensure_philosophy_entries() -> int:
    with db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM philosophy_entries").fetchone()[0]
    if count > 0:
        return count
    return run_philosophy_kb_refresh()

