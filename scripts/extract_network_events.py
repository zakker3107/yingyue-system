#!/usr/bin/env python
"""從新聞中自動提取和分類網路事件"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.core.storage import db_connection


# 網路事件關鍵詞映射
NETWORK_EVENT_KEYWORDS = {
    "security": {
        "keywords": ["breach", "attack", "vulnerability", "exploit", "hack", "malware", "ransomware", "zero-day"],
        "severity": "high"
    },
    "infrastructure": {
        "keywords": ["outage", "downtime", "failure", "collapse", "crash", "dns", "ddos"],
        "severity": "high"
    },
    "policy": {
        "keywords": ["regulation", "ban", "restriction", "law", "fine", "compliance", "gdpr", "ccpa"],
        "severity": "medium"
    },
    "technology": {
        "keywords": ["protocol", "standard", "update", "release", "upgrade", "ipv6", "http3", "web3"],
        "severity": "low"
    },
    "acquisition": {
        "keywords": ["acquire", "acquisition", "merger", "buyout", "takeover", "investment"],
        "severity": "medium"
    },
    "incident": {
        "keywords": ["incident", "emergency", "crisis", "disaster", "accident"],
        "severity": "high"
    }
}


def classify_event(title: str, summary: str, topic: str) -> tuple[str, str] | None:
    """根據新聞內容分類網路事件
    
    返回: (event_type, severity) 或 None
    """
    text = (title + " " + (summary or "")).lower()
    
    for event_type, config in NETWORK_EVENT_KEYWORDS.items():
        for keyword in config["keywords"]:
            if keyword.lower() in text:
                return (event_type, config["severity"])
    
    return None


def extract_events() -> int:
    """從未處理的新聞中提取網路事件"""
    extracted_count = 0
    
    with db_connection() as conn:
        # 取得所有新聞
        news_items = conn.execute(
            """
            SELECT id, title, link, source, topic, published_at, summary
            FROM news_items
            WHERE id NOT IN (SELECT DISTINCT source_news_id FROM network_events WHERE source_news_id IS NOT NULL)
            ORDER BY published_at DESC
            LIMIT 100
            """
        ).fetchall()
        
        for news in news_items:
            classification = classify_event(news["title"], news["summary"], news["topic"])
            
            if classification:
                event_type, severity = classification
                
                # 檢查是否已存在重複事件
                existing = conn.execute(
                    """
                    SELECT id FROM network_events
                    WHERE source_news_id = ? OR (event_name = ? AND event_type = ?)
                    """,
                    (news["id"], news["title"], event_type)
                ).fetchone()
                
                if existing:
                    continue
                
                # 插入新事件
                conn.execute(
                    """
                    INSERT INTO network_events
                    (event_name, event_type, source, source_url, description, event_date, 
                     severity, status, related_topics, source_news_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        news["title"],
                        event_type,
                        news["source"],
                        news["link"],
                        news["summary"],
                        news["published_at"],
                        severity,
                        "active",
                        news["topic"],
                        news["id"],
                        datetime.now().isoformat(),
                        datetime.now().isoformat()
                    )
                )
                extracted_count += 1
                print(f"✓ 提取事件: {event_type} - {news['title'][:50]}...")
        
        conn.commit()
    
    return extracted_count


def main() -> int:
    print("[Extract] 開始從新聞中提取網路事件...")
    
    try:
        count = extract_events()
        print(f"[Done] 成功提取 {count} 個網路事件")
        return 0
    except Exception as e:
        print(f"[Error] 提取失敗: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
