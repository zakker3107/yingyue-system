from __future__ import annotations

from typing import Protocol


class NewsRepository(Protocol):
    def latest(self, limit: int = 10) -> list[dict[str, str]]: ...


class NotesRepository(Protocol):
    def latest(self, limit: int = 20) -> list[dict[str, str]]: ...


class GraphRepository(Protocol):
    def upsert_links(self, links: list[dict[str, str]]) -> int: ...
