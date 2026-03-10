from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.orchestrator import run_pipeline


def test_pipeline_smoke():
    result = run_pipeline()
    assert result["news_items_ingested"] > 0
    assert result["philosophy_entries"] > 0
    assert isinstance(result["trend_summary"], dict)
    assert len(result["trend_summary"]) > 0
    assert "daily_report" in result
    assert Path(result["daily_report"]["markdown_report"]).exists()
    assert Path(result["daily_report"]["news_csv"]).exists()
    assert Path(result["daily_report"]["weekly_observation"]).exists()
    assert Path(result["daily_report"]["thought_links"]).exists()
    assert "strategic_report" in result
    assert Path(result["strategic_report"]["strategic_report"]).exists()
    assert Path(result["strategic_report"]["strategic_report_latest"]).exists()
    assert "agent_pipeline" in result
    assert "agent_output" in result
    assert Path(result["agent_output"]["agent_json"]).exists()
    assert Path(result["agent_output"]["agent_latest_json"]).exists()
    assert "scout" in result["agent_pipeline"]
    assert "analysis" in result["agent_pipeline"]
    assert "synthesis" in result["agent_pipeline"]
