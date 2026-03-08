from __future__ import annotations


def rank_links(links: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(links, key=lambda x: x.get("source", ""))
