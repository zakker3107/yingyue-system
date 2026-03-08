from __future__ import annotations


class PostgresNewsRepository:
    def latest(self, limit: int = 10) -> list[dict[str, str]]:
        raise NotImplementedError("Postgres repository not wired yet")
