from __future__ import annotations

from typing import Any

from agents.analyst_agent import AnalystAgent
from agents.scout_agent import ScoutAgent
from agents.synthesizer_agent import SynthesizerAgent


def run_agent_pipeline(context: dict[str, Any] | None = None) -> dict[str, Any]:
    shared = dict(context or {})

    scout = ScoutAgent().run(shared)
    shared["news_items"] = scout.get("news_items", [])

    analyst = AnalystAgent().run(shared)
    shared["analysis"] = {
        "sentiment": analyst.get("sentiment", {}),
        "trends": analyst.get("trends", {}),
    }

    synth = SynthesizerAgent().run(shared)

    return {
        "scout": scout,
        "analysis": analyst,
        "synthesis": synth,
    }
