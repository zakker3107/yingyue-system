from __future__ import annotations

from typing import Any

from agents.base import BaseAgent
from modules.graph.builder import build_thought_links
from modules.reporting.daily import build_daily_observation


class SynthesizerAgent(BaseAgent):
    name = "synthesizer-agent"

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        news_items = context.get("news_items", [])
        notes = context.get("notes", [])
        analysis = context.get("analysis", {})
        links = build_thought_links(news_items=news_items, notes=notes)
        report = build_daily_observation(news_items=news_items, analysis=analysis, links=links)
        return {"agent": self.name, "thought_links": links, "daily_observation": report}
