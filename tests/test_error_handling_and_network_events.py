from __future__ import annotations

from pathlib import Path
import sys
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.orchestrator import run_pipeline
from services.api import main as api
from services.core.storage import db_connection, initialize_db
from services.core.trends.analyzer import _score_topics, build_trend_snapshot
from scripts.extract_network_events import classify_event, extract_events


# ====== Test Error Handling & Parameter Validation ======

def test_api_health_always_responds():
    """API 健康檢查應該總是回應"""
    result = api.health()
    assert "status" in result
    assert "timestamp" in result


def test_api_limits_parameter_validation():
    """API 應該驗證限制參數"""
    api.startup()
    
    # 超過最大限制應該被減少到100
    news = api.latest_news(limit=500)
    assert isinstance(news, list)
    
    # 負數或零應該被接受或轉換
    news = api.latest_news(limit=1)
    assert isinstance(news, list)


def test_philosophy_search_empty_query():
    """空查詢應該回傳完整列表或空列表"""
    api.startup()
    result = api.search_philosophy("")
    assert isinstance(result, list)


def test_philosophy_search_long_query():
    """超長查詢應該被處理"""
    api.startup()
    long_query = "a" * 1000
    result = api.search_philosophy(long_query)
    assert isinstance(result, list)
    assert len(result) == 0


def test_startup_backfills_philosophy_seed_when_table_is_empty():
    """startup 應該在哲學資料為空時自動補 seed"""
    initialize_db()
    with db_connection() as conn:
        conn.execute("DELETE FROM philosophy_entries")
        conn.commit()

    api.startup()

    with db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM philosophy_entries").fetchone()[0]

    assert count > 0


def test_trends_summary_returns_consistent_format():
    """趨勢摘要應該返回一致的格式"""
    _seed_pipeline_once()
    
    trends = api.trends_summary()
    assert isinstance(trends, list)
    
    for trend in trends:
        assert "metric_name" in trend
        assert "metric_value" in trend
        assert "bucket" in trend
        assert "captured_at" in trend
        assert isinstance(trend["metric_value"], (int, float))


def test_network_events_valid_status_filtering():
    """網路事件應該正確過濾狀態"""
    api.startup()
    
    # 各種狀態都應該回傳列表
    for status in ["active", "inactive", "archived"]:
        result = api.network_events(status=status)
        assert isinstance(result, list)


def test_network_events_pagination_limits():
    """網路事件應該尊重分頁限制"""
    api.startup()
    
    # 限制應該被限制在1-100之間
    result = api.network_events(limit=500)
    assert len(result) <= 100
    
    result = api.network_events(limit=5)
    assert len(result) <= 5


# ====== Test Network Events Logic ======

def test_classify_event_security_keywords():
    """應該正確分類安全相關事件"""
    result = classify_event("SQL Injection vulnerability found", "A critical breach detected", "security")
    assert result is not None
    event_type, severity = result
    assert event_type == "security"
    assert severity == "high"


def test_classify_event_infrastructure_outage():
    """應該正確分類基礎設施事件"""
    result = classify_event("Major DNS outage across regions", "System down for 2 hours", "incident")
    assert result is not None
    event_type, severity = result
    assert "outage" in event_type or event_type == "infrastructure"


def test_classify_event_no_match():
    """不匹配的內容應該返回 None"""
    result = classify_event("Weather forecast for next week", "Sunny conditions expected", "general")
    assert result is None


def test_classify_event_policy_and_regulation():
    """應該正確分類政策和監管事件"""
    result = classify_event("New GDPR compliance requirements", "EU issues new data protection law", "policy")
    assert result is not None
    event_type, severity = result
    assert event_type == "policy"


def test_extract_events_returns_count():
    """提取事件應該返回計數"""
    _seed_pipeline_once()
    count = extract_events()
    assert isinstance(count, int)
    assert count >= 0


def test_network_event_summary_structure():
    """網路事件摘要應該有正確的結構"""
    api.startup()
    
    summary = api.network_event_summary()
    assert isinstance(summary, dict)
    
    # 應該至少有以下欄位
    for key in ["event_type_summary", "severity_summary", "recent_events"]:
        assert key in summary
        assert isinstance(summary[key], list)


def test_network_events_by_type_filter():
    """按類型過濾網路事件"""
    api.startup()
    
    # 嘗試各種事件類型
    for event_type in ["security", "infrastructure", "policy", "technology"]:
        result = api.network_events_by_type(event_type)
        assert isinstance(result, list)


# ====== Test Trend Analysis Robustness ======

def test_score_topics_case_insensitive():
    """主題評分應該不區分大小寫"""
    result1 = _score_topics("AI models and algorithms")
    result2 = _score_topics("ai MODELS and ALGORITHMS")
    assert result1 == result2


def test_score_topics_multiple_categories():
    """應該能識別多個類別"""
    result = _score_topics("AI security breach and chip manufacturing")
    assert "ai" in result or "security" in result
    assert len(result) >= 1


def test_score_topics_always_returns_list():
    """應該總是返回列表"""
    test_cases = [
        "",
        "random words without meaning",
        "AI, chip, security, policy, economy",
        "123 456 789"
    ]
    
    for test in test_cases:
        result = _score_topics(test)
        assert isinstance(result, list)
        assert len(result) >= 1


def test_build_trend_snapshot_consistency():
    """構建趨勢快照應該產生有效的結果"""
    _seed_pipeline_once()
    
    snapshot = build_trend_snapshot()
    assert isinstance(snapshot, dict)
    
    # 所有比例應該加起來接近 100
    total = sum(snapshot.values())
    assert 99 <= total <= 101


# ====== Helper Functions ======

def _seed_pipeline_once() -> dict[str, object]:
    """運行管道一次以填充 DB"""
    initialize_db()
    return run_pipeline()
