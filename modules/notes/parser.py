from __future__ import annotations


def parse_note(title: str, body: str, tags: list[str] | None = None) -> dict[str, str]:
    return {
        "title": title.strip(),
        "body": body.strip(),
        "tags": ",".join(tags or []),
    }
