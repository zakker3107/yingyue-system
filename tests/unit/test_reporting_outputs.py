from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.reporting import strategic
from pipelines.reporting import daily_report


def test_infer_second_order_tags_avoids_false_security_match():
    item = {
        "title": "German philosopher and social critic Jürgen Habermas dies at 96",
        "summary": "One the most influential thinkers in post-war Germany, he linked philosophy and political action throughout his life.",
        "topic": "world",
    }

    tags = daily_report._infer_second_order_tags(item)

    assert "安全風險" not in tags
    assert tags == ["社會信任"]


def test_build_focus_event_cards_prioritizes_material_risk_chain():
    news = [
        {
            "title": "War drives oil market higher as shipping insurers pull back",
            "summary": "Oil prices rise and shipping routes tighten after a new regional strike.",
            "topic": "economy",
            "source": "Reuters",
            "link": "https://example.com/1",
            "published_at": "2026-03-15T00:00:00+00:00",
        },
        {
            "title": "Film awards set for Sunday ceremony",
            "summary": "Studios prepare for a major awards night.",
            "topic": "world",
            "source": "BBC World",
            "link": "https://example.com/2",
            "published_at": "2026-03-15T00:00:00+00:00",
        },
    ]
    trends = [{"bucket": "economy", "metric_value": 42.0}, {"bucket": "ai", "metric_value": 22.0}]

    cards = daily_report._build_focus_event_cards(news, trends)

    assert cards[0]["title"] == "War drives oil market higher as shipping insurers pull back"
    assert "價格壓力" in cards[0]["impacts"]
    assert cards[0]["confidence_score"] > cards[1]["confidence_score"]


def test_strategic_classification_treats_entertainment_as_culture_not_politics():
    item = {
        "title": "Oscars 2026: What to expect, how to watch and who will win",
        "summary": "Major studios and nominees prepare for the ceremony.",
        "topic": "world",
    }

    category = strategic._classify_item(item)

    assert category == "culture"


def test_strategic_observation_line_uses_chinese_topic_labels():
    line = strategic._line_from_observation(
        {
            "observed_date": "2026-03-15",
            "top_topic": "general",
            "second_topic": "ai",
            "sentiment_label": "偏負向",
        }
    )

    assert "主趨勢 綜合" in line
    assert "次軸 AI" in line
