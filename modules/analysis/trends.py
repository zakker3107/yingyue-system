from __future__ import annotations

from collections import Counter


def trend_snapshot(news_items: list[dict[str, str]]) -> dict[str, int]:
    counter = Counter(item.get("topic", "general") for item in news_items)
    return dict(counter)
