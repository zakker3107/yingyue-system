from __future__ import annotations

from services.api import main as existing_api


class LegacyNewsRepository:
    def latest(self, limit: int = 10) -> list[dict[str, str]]:
        return existing_api.latest_news(limit=limit)
