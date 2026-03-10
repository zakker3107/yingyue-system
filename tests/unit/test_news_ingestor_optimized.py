from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.core.ingestion.news_ingestor_optimized import _dedupe_news_batch


def test_dedupe_news_batch_removes_duplicate_news_rows():
    items = [
        {
            "title": "Same title",
            "link": "https://example.com/a",
            "source": "Example",
            "topic": "world",
            "published_at": "2026-03-08T12:00:00+00:00",
            "summary": "first",
        },
        {
            "title": "Same title",
            "link": "https://example.com/a?dup=1",
            "source": "Example",
            "topic": "world",
            "published_at": "2026-03-08T12:00:00+00:00",
            "summary": "duplicate",
        },
        {
            "title": "Another title",
            "link": "https://example.com/b",
            "source": "Example",
            "topic": "tech",
            "published_at": "2026-03-08T13:00:00+00:00",
            "summary": "unique",
        },
    ]

    deduped = _dedupe_news_batch(items)

    assert len(deduped) == 2
    assert deduped[0]["title"] == "Same title"
    assert deduped[1]["title"] == "Another title"
