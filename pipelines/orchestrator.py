from __future__ import annotations

import json
from datetime import datetime, timezone

from core.orchestrator.pipeline import run_agent_pipeline
from pipelines.reporting.daily_report import generate_daily_report
from scripts.activity_rules_runtime import active_rule_ids, has_rule, load_rules
from services.core.ingestion.news_ingestor_optimized import run_news_ingestion
from services.core.kb.philosophy_kb import run_philosophy_kb_refresh
from services.core.settings import REPORT_DIR
from services.core.storage import db_connection, initialize_db
from services.core.trends.analyzer import build_trend_snapshot


def _extract_network_events() -> int:
    """從新聞中提取網路事件"""
    try:
        from scripts.extract_network_events import extract_events

        return extract_events()
    except Exception as e:
        print(f"[Warning] 網路事件提取失敗: {e}")
        return 0


def _latest_news_for_agents(limit: int = 20) -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, source, topic, published_at, summary, link
            FROM news_items
            ORDER BY datetime(published_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _apply_content_dedupe(news_items: list[dict[str, str]], enabled: bool) -> tuple[list[dict[str, str]], int]:
    if not enabled:
        return news_items, 0

    seen_links: set[str] = set()
    deduped: list[dict[str, str]] = []
    removed = 0

    for item in news_items:
        link = str(item.get("link") or "").strip()
        key = link if link else str(item.get("title") or "").strip()
        if not key:
            deduped.append(item)
            continue

        if key in seen_links:
            removed += 1
            continue

        seen_links.add(key)
        deduped.append(item)

    return deduped, removed


def _latest_notes_for_agents(limit: int = 10) -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, summary, keywords
            FROM philosophy_entries
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    notes: list[dict[str, str]] = []
    for row in rows:
        notes.append(
            {
                "title": row["title"],
                "body": row["summary"],
                "tags": row["keywords"],
            }
        )
    return notes


def _write_agent_output(agent_result: dict[str, object], date_label: str) -> dict[str, str]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = REPORT_DIR / f"agent_pipeline_{date_label}.json"
    latest_path = REPORT_DIR / "agent_pipeline_latest.json"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": date_label,
        "agent_pipeline": agent_result,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    dated_path.write_text(text, encoding="utf-8")
    latest_path.write_text(text, encoding="utf-8")

    return {
        "agent_json": str(dated_path),
        "agent_latest_json": str(latest_path),
    }


def run_pipeline() -> dict[str, object]:
    initialize_db()
    news_count = run_news_ingestion()  # 使用優化版本的爬蟲
    philosophy_count = run_philosophy_kb_refresh()
    trend_summary = build_trend_snapshot()
    network_events_count = _extract_network_events()
    report_paths = generate_daily_report()

    rules_payload = load_rules()
    enabled_rule_ids = active_rule_ids(rules_payload)

    news_items = _latest_news_for_agents(limit=20)
    news_items, dedup_removed = _apply_content_dedupe(
        news_items,
        enabled=has_rule(rules_payload, "content-001"),
    )

    agent_result = run_agent_pipeline(
        context={
            "limit": 20,
            "news_items": news_items,
            "notes": _latest_notes_for_agents(limit=10),
        }
    )
    agent_paths = _write_agent_output(agent_result, str(report_paths.get("date", "latest")))

    return {
        "news_items_ingested": news_count,
        "philosophy_entries": philosophy_count,
        "trend_summary": trend_summary,
        "network_events_extracted": network_events_count,
        "daily_report": report_paths,
        "agent_pipeline": agent_result,
        "agent_output": agent_paths,
        "active_rules": enabled_rule_ids,
        "content_dedupe_removed": dedup_removed,
    }
