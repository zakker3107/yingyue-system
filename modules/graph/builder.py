from __future__ import annotations


def build_thought_links(news_items: list[dict[str, str]], notes: list[dict[str, str]]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    top_topic = news_items[0].get("topic", "general") if news_items else "general"
    for note in notes[:5]:
        links.append(
            {
                "source": f"Trend:{top_topic}",
                "target": f"Note:{note.get('title', 'Untitled')}",
                "reason": "shared topic focus",
            }
        )
    return links
