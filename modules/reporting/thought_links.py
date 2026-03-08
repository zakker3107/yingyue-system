from __future__ import annotations


def build_thought_links_report(links: list[dict[str, str]]) -> dict[str, object]:
    return {"items": len(links), "type": "thought_links"}
