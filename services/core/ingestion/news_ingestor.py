from __future__ import annotations

import json
import ssl
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from services.core.settings import RAW_NEWS_PATH, SOURCES_CONFIG
from services.core.storage import db_connection


def _load_config() -> dict[str, Any]:
    with SOURCES_CONFIG.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def _normalize_published(raw: str | None) -> str:
    if not raw:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _fallback_items() -> list[dict[str, str]]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "title": "Global AI policy talks advance in multi-country summit",
            "link": "https://example.org/world-ai-policy",
            "source": "Fallback",
            "topic": "world",
            "published_at": now,
            "summary": "Leaders discussed AI safety standards and data governance cooperation.",
        },
        {
            "title": "Open-source chip design tools gain momentum",
            "link": "https://example.org/open-chip-tools",
            "source": "Fallback",
            "topic": "technology",
            "published_at": now,
            "summary": "Developers report faster iteration cycles for custom accelerators.",
        },
    ]


def _fetch_url(url: str, timeout: int) -> bytes | None:
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "YingYueMVP/0.1"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()
    except Exception:
        return None


def _parse_rss(xml_bytes: bytes, source_name: str, topic: str, max_items: int) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    items: list[dict[str, str]] = []
    for item in root.findall(".//item")[:max_items]:
        title = (item.findtext("title") or "Untitled").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = item.findtext("pubDate") or item.findtext("published") or item.findtext("updated")
        summary = (item.findtext("description") or item.findtext("summary") or "").strip()

        items.append(
            {
                "title": title,
                "link": link,
                "source": source_name,
                "topic": topic,
                "published_at": _normalize_published(pub_date),
                "summary": summary[:500],
            }
        )
    return items


def collect_news() -> list[dict[str, str]]:
    config = _load_config()
    sources = config.get("news_sources", [])
    max_items = int(config.get("collection", {}).get("max_items_per_source", 20))
    timeout_seconds = int(config.get("collection", {}).get("timeout_seconds", 8))

    collected: list[dict[str, str]] = []
    for source in sources:
        xml_data = _fetch_url(source["url"], timeout_seconds)
        if not xml_data:
            continue
        collected.extend(
            _parse_rss(
                xml_data,
                source_name=source["name"],
                topic=source["topic"],
                max_items=max_items,
            )
        )

    if not collected:
        collected = _fallback_items()

    RAW_NEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_NEWS_PATH.open("w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    return collected


def store_news(items: list[dict[str, str]]) -> int:
    with db_connection() as conn:
        conn.execute("DELETE FROM news_items")
        conn.executemany(
            """
            INSERT INTO news_items(title, link, source, topic, published_at, summary)
            VALUES(:title, :link, :source, :topic, :published_at, :summary)
            """,
            items,
        )
        conn.commit()
    return len(items)


def run_news_ingestion() -> int:
    items = collect_news()
    return store_news(items)


