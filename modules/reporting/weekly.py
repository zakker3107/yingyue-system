from __future__ import annotations


def build_weekly_observation(days: list[dict[str, object]]) -> dict[str, object]:
    return {"days": len(days), "summary": "weekly overview"}
