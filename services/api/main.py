from __future__ import annotations

import json
import time
from pathlib import Path
from functools import lru_cache

from services.core.settings import REPORT_DIR
from services.core.storage import db_connection, initialize_db


# 簡單的查詢快取 (LRU)
@lru_cache(maxsize=128)
def _cached_news_query(limit: int, offset: int = 0) -> tuple[tuple, ...]:
    """快取新聞查詢結果 (最多 128 個查詢)"""
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, link, source, topic, published_at, summary
            FROM news_items
            ORDER BY datetime(published_at) DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return tuple(rows)


def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": str(time.time())}


def latest_news(limit: int = 10) -> list[dict[str, str]]:
    """優化：使用快取減少資料庫查詢，並驗證參數"""
    # 參數驗證
    limit = max(1, min(int(limit), 100))  # 限制在 1-100
    
    rows = _cached_news_query(limit, 0)
    return [dict(r) for r in rows]


def search_philosophy(q: str) -> list[dict[str, str]]:
    """搜尋哲學條目，有參數驗證"""
    # 清理查詢字符
    q = str(q).strip()[:500]  # 最多 500 字
    if not q:
        # 空查詢返回最新條目
        with db_connection() as conn:
            rows = conn.execute(
                "SELECT title, author, school, era, summary, keywords FROM philosophy_entries ORDER BY id DESC LIMIT 20"
            ).fetchall()
        return [dict(r) for r in rows]
    
    pattern = f"%{q.lower()}%"
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, author, school, era, summary, keywords
            FROM philosophy_entries
            WHERE lower(title) LIKE ? OR lower(author) LIKE ? OR lower(summary) LIKE ? OR lower(keywords) LIKE ?
            ORDER BY id DESC
            LIMIT 20
            """,
            (pattern, pattern, pattern, pattern),
        ).fetchall()
    return [dict(r) for r in rows]


def trends_summary() -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT metric_name, metric_value, bucket, captured_at
            FROM trend_snapshots
            ORDER BY metric_value DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def _latest_report(pattern: str, report_type: str) -> dict[str, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(REPORT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {"error": f"{report_type} report not found"}

    latest: Path = files[0]
    content = latest.read_text(encoding="utf-8-sig")
    return {
        "type": report_type,
        "path": str(latest),
        "filename": latest.name,
        "content": content,
    }


def _latest_json_report(pattern: str, report_type: str) -> dict[str, object]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(REPORT_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return {"error": f"{report_type} report not found"}

    latest: Path = files[0]
    payload = json.loads(latest.read_text(encoding="utf-8"))
    return {
        "type": report_type,
        "path": str(latest),
        "filename": latest.name,
        "content": payload,
    }


def latest_daily_observation() -> dict[str, str]:
    return _latest_report("daily_report_*.md", "daily_observation")


def latest_weekly_observation() -> dict[str, str]:
    return _latest_report("weekly_observation_*.md", "weekly_observation")


def latest_thought_links() -> dict[str, str]:
    return _latest_report("thought_links_*.md", "thought_links")


def latest_agent_pipeline() -> dict[str, object]:
    if (REPORT_DIR / "agent_pipeline_latest.json").exists():
        return _latest_json_report("agent_pipeline_latest.json", "agent_pipeline")
    return _latest_json_report("agent_pipeline_*.json", "agent_pipeline")


def network_events(event_type: str = "", status: str = "active", limit: int = 20) -> list[dict[str, object]]:
    """查詢網路事件 (Network Events)，含參數驗證
    
    Args:
        event_type: 事件類型篩選 (可選)
        status: 事件狀態篩選，預設為 'active'
        limit: 返回數量限制，最多 100
    """
    # 參數驗證
    event_type = str(event_type).strip()[:100]
    status = str(status).strip()[:50]
    limit = max(1, min(int(limit), 100))
    
    with db_connection() as conn:
        query = "SELECT * FROM network_events WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
        
        query += " ORDER BY event_date DESC LIMIT ?"
        params.append(limit)
        
        rows = conn.execute(query, params).fetchall()
    
    return [dict(r) for r in rows]


def network_event_summary() -> dict[str, object]:
    """獲取網路事件摘要統計"""
    with db_connection() as conn:
        # 事件類型統計
        event_types = conn.execute(
            """
            SELECT event_type, COUNT(*) as count, MAX(event_date) as latest_date
            FROM network_events
            WHERE status = 'active'
            GROUP BY event_type
            ORDER BY count DESC
            """
        ).fetchall()
        
        # 嚴重程度統計
        severity_stats = conn.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM network_events
            WHERE status = 'active'
            GROUP BY severity
            """
        ).fetchall()
        
        # 最近活動事件
        recent_events = conn.execute(
            """
            SELECT id, event_name, event_type, severity, event_date
            FROM network_events
            WHERE status = 'active'
            ORDER BY event_date DESC
            LIMIT 10
            """
        ).fetchall()
    
    return {
        "event_type_summary": [dict(r) for r in event_types],
        "severity_summary": [dict(r) for r in severity_stats],
        "recent_events": [dict(r) for r in recent_events],
    }


def network_events_by_type(event_type: str, limit: int = 20) -> list[dict[str, object]]:
    """按事件類型查詢網路事件"""
    return network_events(event_type=event_type, limit=limit)


def startup() -> None:
    initialize_db()
