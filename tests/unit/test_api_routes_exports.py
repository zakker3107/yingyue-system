from __future__ import annotations

from apps.api import routes


EXPECTED_EXPORTS = {
    "assistant_context",
    "health",
    "latest_agent_pipeline",
    "latest_daily_observation",
    "latest_news",
    "latest_strategic_report",
    "latest_thought_links",
    "latest_weekly_observation",
    "monitor_snapshot",
    "network_event_summary",
    "network_events",
    "network_events_by_type",
    "search_philosophy",
    "startup",
    "station_summary",
    "task_overview",
    "trends_summary",
}


def test_routes_exports_match_public_api_surface():
    assert set(routes.__all__) == EXPECTED_EXPORTS

    for name in EXPECTED_EXPORTS:
        assert hasattr(routes, name)
