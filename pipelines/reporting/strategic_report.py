from __future__ import annotations

from datetime import datetime, timezone

from modules.reporting.strategic import build_strategic_weekly_report, week_label_from_date
from services.core.settings import REPORT_DIR
from services.core.storage import db_connection


def _fetch_recent_news(limit: int = 20) -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, source, topic, published_at, summary, link
            FROM news_items
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _fetch_recent_trends(limit: int = 5) -> list[dict[str, object]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT bucket, metric_value, captured_at
            FROM trend_snapshots
            ORDER BY metric_value DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _fetch_observations(limit: int = 7) -> list[dict[str, object]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT observed_date, sentiment_score, sentiment_label, top_topic, second_topic, key_takeaway
            FROM observation_logs
            ORDER BY observed_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def generate_strategic_weekly_report(report_date: str | None = None) -> dict[str, str]:
    now = datetime.now(timezone.utc)
    date_label = report_date or now.date().isoformat()
    week_label = week_label_from_date(date_label)

    observations = _fetch_observations(limit=7)
    trends = _fetch_recent_trends(limit=5)
    news = _fetch_recent_news(limit=20)

    markdown = build_strategic_weekly_report(
        week_label=week_label,
        generated_at=now.isoformat(),
        observations=observations,
        trends=trends,
        news=news,
    )

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    dated_path = REPORT_DIR / f"strategic_report_{week_label}.md"
    latest_path = REPORT_DIR / "strategic_report_latest.md"
    dated_path.write_text(markdown, encoding="utf-8-sig")
    latest_path.write_text(markdown, encoding="utf-8-sig")

    return {
        "date": date_label,
        "week": week_label,
        "strategic_report": str(dated_path),
        "strategic_report_latest": str(latest_path),
    }
