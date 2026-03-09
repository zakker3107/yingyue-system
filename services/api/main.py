from __future__ import annotations

import json
import os
import time
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from services.core.settings import REPORT_DIR
from services.core.storage import db_connection, initialize_db

TASK_NAME = os.getenv("YINGYUE_TASK_NAME", "YingYue-Daily-Ops")

@lru_cache(maxsize=128)
def _cached_news_query(limit: int, offset: int = 0) -> tuple[tuple, ...]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, link, source, topic, published_at, summary
            FROM news_items
            ORDER BY published_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return tuple(rows)


def health() -> dict[str, str]:
    return {"status": "ok", "timestamp": str(time.time())}


def latest_news(limit: int = 10) -> list[dict[str, str]]:
    limit = max(1, min(int(limit), 100))
    return [dict(r) for r in _cached_news_query(limit, 0)]


def search_philosophy(q: str) -> list[dict[str, str]]:
    q = str(q).strip()[:500]
    if not q:
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
    files = list(REPORT_DIR.glob(pattern))
    if not files:
        return {"error": f"{report_type} report not found"}
    latest: Path = max(files, key=lambda p: p.stat().st_mtime)
    return {
        "type": report_type,
        "path": str(latest),
        "filename": latest.name,
        "content": latest.read_text(encoding="utf-8-sig"),
    }


def _latest_json_report(pattern: str, report_type: str) -> dict[str, object]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(REPORT_DIR.glob(pattern))
    if not files:
        return {"error": f"{report_type} report not found"}
    latest: Path = max(files, key=lambda p: p.stat().st_mtime)
    return {
        "type": report_type,
        "path": str(latest),
        "filename": latest.name,
        "content": json.loads(latest.read_text(encoding="utf-8")),
    }


def _latest_report_meta(pattern: str, report_type: str) -> dict[str, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    files = list(REPORT_DIR.glob(pattern))
    if not files:
        return {"error": f"{report_type} report not found"}
    latest: Path = max(files, key=lambda p: p.stat().st_mtime)
    return {
        "type": report_type,
        "path": str(latest),
        "filename": latest.name,
        "updated_at": datetime.fromtimestamp(latest.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
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
    event_type = str(event_type).strip()[:100]
    status = str(status).strip()[:50]
    limit = max(1, min(int(limit), 100))
    with db_connection() as conn:
        query = "SELECT id, event_name, event_type, source, source_url, description, event_date, severity, status, related_topics, tags, source_news_id, created_at, updated_at FROM network_events WHERE 1=1"
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
    with db_connection() as conn:
        event_types = conn.execute(
            """
            SELECT event_type, COUNT(*) as count, MAX(event_date) as latest_date
            FROM network_events
            WHERE status = 'active'
            GROUP BY event_type
            ORDER BY count DESC
            """
        ).fetchall()
        severity_stats = conn.execute(
            """
            SELECT severity, COUNT(*) as count
            FROM network_events
            WHERE status = 'active'
            GROUP BY severity
            """
        ).fetchall()
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
    return network_events(event_type=event_type, limit=limit)


def station_summary() -> dict[str, object]:
    with db_connection() as conn:
        table_counts = conn.execute(
            """
            SELECT
              (SELECT COUNT(*) FROM news_items) AS news_count,
              (SELECT COUNT(*) FROM trend_snapshots) AS trend_count,
              (SELECT COUNT(*) FROM philosophy_entries) AS philosophy_count,
              (SELECT COUNT(*) FROM network_events WHERE status = 'active') AS active_event_count
            """
        ).fetchone()
        latest_news_row = conn.execute(
            """
            SELECT title, source, topic, published_at
            FROM news_items
            ORDER BY published_at DESC
            LIMIT 1
            """
        ).fetchone()
        top_trends = conn.execute(
            """
            SELECT metric_name, metric_value, bucket, captured_at
            FROM trend_snapshots
            ORDER BY captured_at DESC, metric_value DESC
            LIMIT 5
            """
        ).fetchall()
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "counts": dict(table_counts) if table_counts else {},
        "latest_news": dict(latest_news_row) if latest_news_row else None,
        "top_trends": [dict(r) for r in top_trends],
        "reports": {
            "daily": _latest_report_meta("daily_report_*.md", "daily_observation"),
            "weekly": _latest_report_meta("weekly_observation_*.md", "weekly_observation"),
            "thought_links": _latest_report_meta("thought_links_*.md", "thought_links"),
            "agent_pipeline": _latest_report_meta("agent_pipeline_*.json", "agent_pipeline"),
            "status": _latest_report_meta("status_report.md", "status_report"),
        },
    }


def task_overview() -> dict[str, object]:
    reports = station_summary().get("reports", {})
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "tasks": [
            {"id": "daily-ops", "name": "Daily Ops", "kind": "scheduled", "status": "READY", "schedule": "Every day 08:30", "outputs": [reports.get("daily", {}), reports.get("status", {})]},
            {"id": "health-report", "name": "Health Report", "kind": "manual", "status": "AVAILABLE", "schedule": "On demand", "outputs": [reports.get("status", {})]},
            {"id": "agent-pipeline", "name": "Agent Pipeline Snapshot", "kind": "artifact", "status": "AVAILABLE", "schedule": "After pipeline run", "outputs": [reports.get("agent_pipeline", {})]},
        ],
    }


def assistant_context() -> dict[str, object]:
    station = station_summary()
    top_trends = station.get("top_trends", [])[:3]
    latest = station.get("latest_news") or {}
    prompts = []
    if latest:
        prompts.append(f"整理最新新聞《{latest.get('title', '')}》對今日觀察的影響")
    for trend in top_trends:
        prompts.append(f"分析趨勢 {trend.get('metric_name', '')} 的近期變化")
    prompts.append("檢查每日排程是否有缺失並給出補跑建議")
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "task_name": TASK_NAME,
        "summary": {"latest_news": latest, "top_trends": top_trends, "report_status": station.get("reports", {})},
        "suggested_prompts": prompts,
    }


def monitor_snapshot() -> dict[str, object]:
    station = station_summary()
    network = network_event_summary()
    counts = station.get("counts", {})
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "health": health(),
        "counts": counts,
        "network": {
            "active_events": counts.get("active_event_count", 0),
            "severity_summary": network.get("severity_summary", []),
            "recent_events": network.get("recent_events", [])[:5],
        },
        "reports": station.get("reports", {}),
    }


def startup() -> None:
    initialize_db()
