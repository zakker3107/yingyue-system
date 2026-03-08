from __future__ import annotations


def build_daily_observation(
    news_items: list[dict[str, str]],
    analysis: dict[str, object],
    links: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "headline_count": len(news_items),
        "analysis": analysis,
        "link_count": len(links),
    }
