from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.orchestrator import run_pipeline
from services.api import main as api

# build a lightweight FastAPI app for end-to-end endpoint testing
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/health")
def _health():
    return api.health()

@app.get("/news")
def _news(limit: int = 10):
    return api.latest_news(limit=limit)

@app.get("/trends")
def _trends():
    return api.trends_summary()

@app.get("/philosophy/search")
def _philosophy_search(q: str):
    return api.search_philosophy(q)

@app.get("/reports/daily")
def _daily():
    return api.latest_daily_observation()

@app.get("/network/events")
def _network(event_type: str = "", status: str = "active", limit: int = 20):
    return api.network_events(event_type=event_type, status=status, limit=limit)

client = TestClient(app)




def _seed_pipeline_once() -> dict[str, object]:
    return run_pipeline()



def test_daily_report_files_exist_and_have_header():
    result = _seed_pipeline_once()
    daily_report = result["daily_report"]

    md_path = Path(daily_report["markdown_report"])
    csv_path = Path(daily_report["news_csv"])
    weekly_path = Path(daily_report["weekly_observation"])
    thought_path = Path(daily_report["thought_links"])

    assert md_path.exists()
    assert csv_path.exists()
    assert weekly_path.exists()
    assert thought_path.exists()

    content = md_path.read_text(encoding="utf-8-sig")
    assert "# 影月系統每日觀察" in content
    assert "## 世界新聞整理" in content



def test_api_response_shapes():
    api.startup()

    health = api.health()
    assert health.get("status") == "ok"

    news = api.latest_news(limit=3)
    assert isinstance(news, list)
    if news:
        assert {"title", "source", "topic", "published_at"}.issubset(news[0].keys())

    trends = api.trends_summary()
    assert isinstance(trends, list)
    if trends:
        assert {"metric_name", "metric_value", "bucket", "captured_at"}.issubset(trends[0].keys())


def test_http_endpoints():
    # perform a few HTTP-style requests against the lightweight FastAPI app
    api.startup()

    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

    r = client.get("/news", params={"limit": 2})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = client.get("/trends")
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = client.get("/philosophy/search", params={"q": "ethics"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    r = client.get("/reports/daily")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)

    # network events should return list even if empty
    r = client.get("/network/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)



def test_philosophy_search_unlikely_query_returns_list():
    api.startup()
    result = api.search_philosophy("zzzz_unlikely_hit_20260306")
    assert isinstance(result, list)
    assert len(result) <= 20


def test_score_topics_logic():
    # core helper for trend scoring should match expected topics
    from services.core.trends.analyzer import _score_topics

    assert _score_topics("AI model and security breach") == ["ai", "security"]
    assert _score_topics("Completely unrelated words") == ["general"]


def test_agent_helpers_and_output():
    # ensure pipeline has at least one run to populate DB
    result = _seed_pipeline_once()
    # verify helpers return list shapes and do not error
    from pipelines.orchestrator import _latest_news_for_agents, _latest_notes_for_agents, _write_agent_output

    news_list = _latest_news_for_agents(limit=5)
    assert isinstance(news_list, list)

    notes_list = _latest_notes_for_agents(limit=5)
    assert isinstance(notes_list, list)

    # write custom payload and verify files exist
    agent_paths = _write_agent_output({"foo": "bar"}, "testlabel")
    assert Path(agent_paths["agent_json"]).exists()
    assert Path(agent_paths["agent_latest_json"]).exists()


def test_report_endpoints_and_network_events():
    api.startup()

    # report endpoints should return dicts with expected keys
    for func in (
        api.latest_daily_observation,
        api.latest_weekly_observation,
        api.latest_thought_links,
        api.latest_agent_pipeline,
    ):
        resp = func()
        assert isinstance(resp, dict)
        assert "type" in resp
        assert "content" in resp or "error" in resp

    # network-related endpoints should be callable even if DB has no events
    assert isinstance(api.network_events(), list)
    assert isinstance(api.network_event_summary(), dict)
    assert isinstance(api.network_events_by_type("any"), list)

