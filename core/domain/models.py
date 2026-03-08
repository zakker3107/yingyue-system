from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NewsItem:
    title: str
    source: str
    topic: str
    published_at: str
    summary: str
    link: str


@dataclass(slots=True)
class ThoughtNote:
    title: str
    body: str
    tags: list[str]


@dataclass(slots=True)
class KnowledgeLink:
    source: str
    target: str
    reason: str
