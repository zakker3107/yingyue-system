from __future__ import annotations


def normalize_news_item(item: dict[str, str]) -> dict[str, str]:
    return {
        "title": item.get("title", "").strip(),
        "source": item.get("source", "").strip(),
        "topic": item.get("topic", "general").strip() or "general",
        "published_at": item.get("published_at", "").strip(),
        "summary": item.get("summary", "").strip(),
        "link": item.get("link", "").strip(),
    }
