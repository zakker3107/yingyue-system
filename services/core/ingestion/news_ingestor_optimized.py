"""性能優化版本的新聞爬蟲 - 並發、快取、批量操作"""

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


# 簡單的記憶體快取 (TTL: 10 分鐘)
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 600  # 秒


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
    """從快取中獲取數據"""
    with _cache_lock:
        if key in _cache:
            value, expires_at = _cache[key]
            if time.time() < expires_at:
                return value
            del _cache[key]
    return None


def _set_cache(key: str, value: Any, ttl: int = CACHE_TTL) -> None:
    """設定快取數據"""
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
    """優化：使用快取減少重複請求"""
    cache_key = f"url:{md5(url.encode()).hexdigest()}"
    cached = _get_cached(cache_key)
    if cached:
        return cached
    
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers={"User-Agent": "YingYueMVP/0.1"})
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            data = resp.read()
            _set_cache(cache_key, data, ttl=300)  # 5 分鐘快取
            return data
    except Exception:
        return None


def _parse_rss(xml_bytes: bytes, source_name: str, topic: str, max_items: int) -> list[dict[str, str]]:
    """優化：改進 XML 解析性能"""
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

        if title and link:  # 只保存有效項目
            items.append({
                "title": title,
                "link": link,
                "source": source_name,
                "topic": topic,
                "published_at": _normalize_published(pub_date),
                "summary": summary[:500],
            })
            item_count += 1
    
    return items


def collect_news_concurrent() -> list[dict[str, str]]:
    """優化：並發爬蟲，使用 ThreadPoolExecutor"""
    config = _load_config()
    sources = config.get("news_sources", [])
    max_items = int(config.get("collection", {}).get("max_items_per_source", 20))
    timeout_seconds = int(config.get("collection", {}).get("timeout_seconds", 8))
    max_workers = min(len(sources), 5)  # 最多 5 個並發線程

    collected: list[dict[str, str]] = []
    results = []

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
            
            if xml_data:
                items = _parse_rss(
                    xml_data,
                    source_name=source_info["source"],
                    topic=source_info["topic"],
                    max_items=max_items,
                )
                results.extend(items)

    collected = results if results else _fallback_items()

    # 優化：直接寫文件，不需額外排序
    RAW_NEWS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RAW_NEWS_PATH.open("w", encoding="utf-8") as f:
        json.dump(collected, f, ensure_ascii=False, indent=2)

    return collected


def store_news_optimized(items: list[dict[str, str]]) -> int:
    """優化：使用 INSERT OR REPLACE 替代 DELETE + INSERT"""
    with db_connection() as conn:
        # 先清理超過 7 天的舊新聞
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        conn.execute("DELETE FROM news_items WHERE published_at < ?", (cutoff_date,))
        
        # 使用 INSERT OR REPLACE 替代 DELETE
        conn.executemany(
            """
            INSERT OR REPLACE INTO news_items(title, link, source, topic, published_at, summary, inserted_at)
            VALUES(:title, :link, :source, :topic, :published_at, :summary, CURRENT_TIMESTAMP)
            """,
            items,
        )
        conn.commit()
    
    return len(items)


def run_news_ingestion() -> int:
    """改進的新聞爬蟲管道"""
    items = collect_news_concurrent()  # 使用並發版本
    return store_news_optimized(items)  # 使用優化的存儲
