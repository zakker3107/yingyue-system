from __future__ import annotations


def topics_from_texts(texts: list[str]) -> list[str]:
    return ["general"] if not texts else ["technology", "society"]
