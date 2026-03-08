from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from modules.news.collectors.rss import collect_rss_news


class ScoutAgent(BaseAgent):
    name = "scout-agent"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        existing = context.get("news_items")
        if isinstance(existing, list) and existing:
            return {"agent": self.name, "news_items": existing, "source": "pipeline-context"}

        limit = int(context.get("limit", 10))
        items = collect_rss_news(limit=limit)
        return {"agent": self.name, "news_items": items, "source": "collector"}
