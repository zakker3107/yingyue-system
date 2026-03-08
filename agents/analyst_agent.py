from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from modules.analysis.sentiment import sentiment_snapshot
from modules.analysis.trends import trend_snapshot


class AnalystAgent(BaseAgent):
    name = "analyst-agent"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        news_items = context.get("news_items", [])
        return {
            "agent": self.name,
            "sentiment": sentiment_snapshot(news_items),
            "trends": trend_snapshot(news_items),
        }
