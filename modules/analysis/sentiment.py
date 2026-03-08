from __future__ import annotations

POSITIVE_WORDS = [
    "growth",
    "breakthrough",
    "progress",
    "cooperate",
    "stability",
    "optimism",
    "improve",
    "recovery",
    "gain",
    "advance",
]

NEGATIVE_WORDS = [
    "war",
    "crisis",
    "risk",
    "conflict",
    "decline",
    "attack",
    "fear",
    "volatile",
    "slowdown",
    "inflation",
]


def _label_sentiment(score: float) -> str:
    if score >= 0.2:
        return "偏正向"
    if score <= -0.2:
        return "偏負向"
    return "中性"


def sentiment_snapshot(news_items: list[dict[str, str]]) -> dict[str, float | str | int]:
    text = " ".join(
        f"{item.get('title', '')} {item.get('summary', '')}".lower()
        for item in news_items
    )
    positive_hits = sum(text.count(word) for word in POSITIVE_WORDS)
    negative_hits = sum(text.count(word) for word in NEGATIVE_WORDS)
    denominator = positive_hits + negative_hits
    score = 0.0 if denominator == 0 else (positive_hits - negative_hits) / denominator

    return {
        "score": round(score, 3),
        "label": _label_sentiment(score),
        "positive_hits": positive_hits,
        "negative_hits": negative_hits,
    }

