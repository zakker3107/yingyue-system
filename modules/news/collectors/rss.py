from __future__ import annotations

from services.core.ingestion.news_ingestor import collect_news


def collect_rss_news(limit: int = 10) -> list[dict[str, str]]:
    return collect_news()[:limit]
