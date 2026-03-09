"""Optimized concurrent RSS ingestion with bounded deduplication."""

from __future__ import annotations

import json
import ssl
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from hashlib import md5
from typing import Any

from services.core.settings import RAW_NEWS_PATH, SOURCES_CONFIG
from services.core.storage import db_connection


_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 600


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


def _get_cached(key: str) -> Any | None:
    with _cache_lock:
        if key in _cache:
            value, expires_at = _cache[key]
            if time.time() < expires_at:
                return value
            del _cache[key]
    return None


def _set_cache(key: str, value: Any, ttl: int = CACHE_TTL) -> None:
    with _cache_lock:
        _cache[key] = (value, time.time() + ttl)


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
    cache_key = f"url:{md5(url.encode()).hexdigest()}"
    cached = _get_cached(cache_key)
    if cached:
        return cached

    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "YingYueMVP/0.1"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
            _set_cache(cache_key, data, ttl=300)
            return data
    except Exception:
        return None


def _parse_rss(xml_bytes: bytes, source_name: str, topic: str, max_items: int) -> list[dict[str, str]]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []

    items: list[dict[str, str]] = []
    item_count = 0

    for item in root.findall(".//item"):
        if item_count >= max_items:
            break

        title = (item.findtext("title") or "Untitled").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = item.findtext("pubDate") or item.findtext("published") or item.findtext("updated")
        summary = (item.findtext("description") or item.findtext("summary") or "").strip()

        if title and link:
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
            item_count += 1

    return items


def _dedupe_news_batch(items: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    for item in items:
        key = (
            str(item.get("source") or "").strip(),
            str(item.get("title") or "").strip(),
            str(item.get("published_at") or "").strip(),
        )
        if not all(key):
            deduped.append(item)
            continue
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def collect_news_concurrent() -> list[dict[str, str]]:
    config = _load_config()
    sources = config.get("news_sources", [])
    max_items = int(config.get("collection", {}).get("max_items_per_source", 20))
    timeout_seconds = int(config.get("collection", {}).get("timeout_seconds", 8))
    max_workers = max(1, min(len(sources), 5))

    results: list[dict[str, str]] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_fetch_url, source["url"], timeout_seconds): {
                "source": source["name"],
                "topic": source["topic"],
            }
            for source in sources
        }

        for future in as_completed(futures):
            source_info = futures[future]
            xml_data = future.result()
            if not xml_data:
                continue
            results.extend(
                _parse_rss(
                    xml_data,
                    source_name=source_info["source"],
                    topic=source_info["topic"],
                    max_items=max_items,
                )
            )

    collected = _dedupe_news_batch(results) if results else _fallback_items()

    RAW_NEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_NEWS_PATH.open("w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    return collected


def store_news_optimized(items: list[dict[str, str]]) -> int:
    deduped_items = _dedupe_news_batch(items)
    with db_connection() as conn:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        conn.execute("DELETE FROM news_items WHERE published_at < ?", (cutoff_date,))
        conn.executemany(
            """
            INSERT INTO news_items(title, link, source, topic, published_at, summary, inserted_at)
            VALUES(:title, :link, :source, :topic, :published_at, :summary, CURRENT_TIMESTAMP)
            ON CONFLICT(source, title, published_at) DO UPDATE SET
                link = excluded.link,
                topic = excluded.topic,
                summary = excluded.summary,
                inserted_at = CURRENT_TIMESTAMP
            """,
            deduped_items,
        )
        conn.commit()

    return len(deduped_items)


def run_news_ingestion() -> int:
    items = collect_news_concurrent()
    return store_news_optimized(items)
