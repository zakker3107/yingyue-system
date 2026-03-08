from __future__ import annotations


class ChromaStore:
    def upsert(self, records: list[dict[str, str]]) -> int:
        return len(records)
