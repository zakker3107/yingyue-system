from __future__ import annotations


def link_note_to_topic(note: dict[str, str], topic: str) -> dict[str, str]:
    return {
        "source": f"Note:{note.get('title', '')}",
        "target": f"Trend:{topic}",
        "reason": "note-topic semantic overlap",
    }
