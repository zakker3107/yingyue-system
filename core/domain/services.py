from __future__ import annotations

from core.domain.models import KnowledgeLink, NewsItem, ThoughtNote


def to_news_item(raw: dict[str, str]) -> NewsItem:
    return NewsItem(
        title=raw.get("title", ""),
        source=raw.get("source", ""),
        topic=raw.get("topic", "general"),
        published_at=raw.get("published_at", ""),
        summary=raw.get("summary", ""),
        link=raw.get("link", ""),
    )


def to_note(raw: dict[str, str]) -> ThoughtNote:
    tags = [tag.strip() for tag in raw.get("tags", "").split(",") if tag.strip()]
    return ThoughtNote(title=raw.get("title", ""), body=raw.get("body", ""), tags=tags)


def to_link(raw: dict[str, str]) -> KnowledgeLink:
    return KnowledgeLink(
        source=raw.get("source", ""),
        target=raw.get("target", ""),
        reason=raw.get("reason", ""),
    )
