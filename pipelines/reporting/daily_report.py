from __future__ import annotations

import csv
import re
from collections import Counter
from datetime import datetime

from modules.analysis.sentiment import sentiment_snapshot
from services.core.settings import REPORT_DIR
from services.core.storage import db_connection

TECH_SIGNAL_KEYWORDS = {
    "ai_models": ["ai", "model", "agent", "llm", "inference"],
    "chips_compute": ["chip", "gpu", "semiconductor", "accelerator"],
    "security_governance": ["security", "policy", "regulation", "safety"],
    "dev_platform": ["open-source", "developer", "platform", "tooling"],
}

TOPIC_LABELS = {
    "ai": "AI",
    "chip": "晶片",
    "policy": "政策",
    "security": "安全",
    "economy": "經濟",
    "general": "綜合",
    "world": "世界",
    "technology": "科技",
}

SECOND_ORDER_IMPACT_RULES = {
    "供應鏈": {
        "include": ["supply", "ship", "factory", "export", "shortage", "cargo", "port", "logistics"],
        "exclude": ["scholarship", "relationship", "championship"],
    },
    "價格壓力": {
        "include": ["price", "prices", "inflation", "cost", "market", "tariff", "fuel"],
        "exclude": ["prize", "priced in"],
    },
    "政策反應": {
        "include": ["law", "policy", "regulation", "sanction", "ban", "tariff", "ceasefire talks"],
        "exclude": ["policy maker profile"],
    },
    "安全風險": {
        "include": ["war", "attack", "terror", "gunfire", "explosion", "missile", "strike", "bombardment"],
        "exclude": ["cybersecurity earnings", "security software", "post-war", "postwar"],
    },
    "社會信任": {
        "include": ["public", "election", "embassy", "police", "protest", "court", "compensation", "rights"],
        "exclude": ["publicity", "publicist"],
    },
    "平台治理": {
        "include": ["ai", "platform", "model", "online", "algorithm", "moderation", "data", "privacy"],
        "exclude": ["air india", "daily mail online"],
    },
}

EVENT_TYPE_RULES = {
    "地緣政治": {
        "include": ["war", "strike", "missile", "attack", "ceasefire", "military", "border", "bombardment"],
        "exclude": ["post-war", "postwar"],
    },
    "政策監管": {
        "include": ["policy", "regulation", "law", "tariff", "sanction", "crackdown", "government"],
        "exclude": ["policy debate show"],
    },
    "產業科技": {
        "include": ["ai", "model", "chip", "platform", "software", "data", "robot", "compute"],
        "exclude": ["aid"],
    },
    "市場供應": {
        "include": ["market", "price", "supply", "factory", "ship", "oil", "inflation", "trade"],
        "exclude": ["supermarket"],
    },
    "社會治理": {
        "include": ["police", "court", "protest", "school", "hospital", "compensation", "trust"],
        "exclude": [],
    },
    "文化體育": {
        "include": ["oscars", "football", "world cup", "film", "award", "sport", "festival"],
        "exclude": [],
    },
}

TOPIC_EVENT_HINTS = {
    "ai": ("產業科技", "部署速度、模型成本、治理限制"),
    "technology": ("產業科技", "平台能力、資料治理、基礎設施壓力"),
    "economy": ("市場供應", "價格傳導、供應鏈摩擦、政策回應"),
    "policy": ("政策監管", "政策落地、執法尺度、跨部門協調"),
    "security": ("地緣政治", "安全擴散、外溢風險、制度韌性"),
    "world": ("社會治理", "社會信任、公共治理、跨境連動"),
    "general": ("市場供應", "價格、政策與安全三線是否互相傳導"),
}


def _fetch_news(limit: int = 10) -> list[dict[str, str]]:
    raw_limit = max(limit * 4, limit)
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, source, topic, published_at, summary, link
            FROM news_items
            ORDER BY published_at DESC
            LIMIT ?
            """,
            (raw_limit,),
        ).fetchall()

    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in [dict(r) for r in rows]:
        link_key = str(item.get("link") or "").strip().lower()
        title_key = str(item.get("title") or "").strip().lower()
        source_key = str(item.get("source") or "").strip().lower()
        identity = link_key or f"{title_key}|{source_key}"
        if identity and identity in seen:
            continue
        if identity:
            seen.add(identity)
        deduped.append(item)
        if len(deduped) >= limit:
            break
    return deduped


def _fetch_trends() -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT bucket, metric_value, captured_at
            FROM trend_snapshots
            ORDER BY metric_value DESC
            """
        ).fetchall()
    return [dict(r) for r in rows]


def _fetch_philosophy(limit: int = 3) -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, author, school, era, summary, keywords
            FROM philosophy_entries
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _fetch_recent_observations(limit: int = 3) -> list[dict[str, str]]:
    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT observed_date, sentiment_score, sentiment_label, top_topic, second_topic, key_takeaway
            FROM observation_logs
            ORDER BY observed_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def _label_sentiment(score: float) -> str:
    if score >= 0.2:
        return "偏正向"
    if score <= -0.2:
        return "偏負向"
    return "中性"


def _analyze_sentiment(news: list[dict[str, str]]) -> dict[str, float | str | int]:
    snapshot = sentiment_snapshot(news)
    score = float(snapshot["score"])
    return {
        "score": score,
        "label": _label_sentiment(score),
        "positive_hits": int(snapshot["positive_hits"]),
        "negative_hits": int(snapshot["negative_hits"]),
    }


def _analyze_tech_signals(news: list[dict[str, str]]) -> list[tuple[str, int]]:
    counter: Counter[str] = Counter()
    for item in news:
        text = f"{item['title']} {item['summary']}".lower()
        for signal, keywords in TECH_SIGNAL_KEYWORDS.items():
            if any(keyword in text for keyword in keywords):
                counter[signal] += 1

    if not counter:
        return [("general_technology", 0)]
    return counter.most_common(4)


def _format_ratio(positive_hits: int, negative_hits: int) -> str:
    if positive_hits == 0 and negative_hits == 0:
        return "0:0"
    return f"{positive_hits}:{negative_hits}"


def _topic_name(bucket: str) -> str:
    return TOPIC_LABELS.get(bucket, bucket)


def _contains_keyword(text: str, token: str) -> bool:
    if " " in token:
        return token in text
    return re.search(rf"\b{re.escape(token)}\b", text) is not None


def _match_rule(text: str, include: list[str], exclude: list[str]) -> bool:
    has_include = any(_contains_keyword(text, token) for token in include)
    has_exclude = any(_contains_keyword(text, token) for token in exclude)
    return has_include and not has_exclude


def _top_topic_pair(trends: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    top_trend = trends[0] if trends else {"bucket": "general", "metric_value": 0}
    second_trend = trends[1] if len(trends) > 1 else {"bucket": "general", "metric_value": 0}
    return top_trend, second_trend


def _classify_event_type(item: dict[str, str]) -> str:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    scores = {
        label: (
            sum(1 for token in rule["include"] if _contains_keyword(text, token))
            if not any(_contains_keyword(text, token) for token in rule["exclude"])
            else 0
        )
        for label, rule in EVENT_TYPE_RULES.items()
    }
    category, score = max(scores.items(), key=lambda pair: pair[1])
    if score > 0:
        return category

    topic = str(item.get("topic") or "general")
    return TOPIC_EVENT_HINTS.get(topic, TOPIC_EVENT_HINTS["general"])[0]


def _infer_second_order_tags(item: dict[str, str]) -> list[str]:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    tags = [
        label
        for label, rule in SECOND_ORDER_IMPACT_RULES.items()
        if _match_rule(text, rule["include"], rule["exclude"])
    ]
    if not tags:
        topic = str(item.get("topic") or "general")
        if topic in {"technology", "ai"}:
            tags = ["平台治理"]
        elif topic in {"world", "policy"}:
            tags = ["社會信任"]
        elif topic == "economy":
            tags = ["價格壓力"]
        else:
            tags = ["持續觀察"]
    return tags[:3]


def _build_second_order_impact_lines(news: list[dict[str, str]]) -> list[str]:
    lines: list[str] = []
    for item in news[:5]:
        tags = "、".join(_infer_second_order_tags(item))
        lines.append(f"〈{item['title']}〉 -> {tags}")
    return lines or ["今日沒有可標記的新聞樣本。"]


def _build_trend_pulse(samples: list[dict[str, str]]) -> list[str]:
    if not samples:
        return ["近三日尚無資料，無法判讀短期脈動。"]
    if len(samples) == 1:
        sample = samples[0]
        return [f"目前只有 {sample['observed_date']} 的觀察資料，先累積至少三天再看轉向。"]

    latest = samples[0]
    previous = samples[1]
    lines: list[str] = []

    if latest["top_topic"] == previous["top_topic"]:
        lines.append(f"主趨勢連續兩日維持在 {latest['top_topic']}，短線敘事仍未切換。")
    else:
        lines.append(f"主趨勢由 {previous['top_topic']} 轉為 {latest['top_topic']}，表示焦點正在重排。")

    sentiment_delta = round(float(latest["sentiment_score"]) - float(previous["sentiment_score"]), 3)
    if sentiment_delta < -0.15:
        lines.append(f"情緒較前一日再走弱 {abs(sentiment_delta)}，風險敘事正在增強。")
    elif sentiment_delta > 0.15:
        lines.append(f"情緒較前一日回升 {sentiment_delta}，市場與敘事壓力略有緩和。")
    else:
        lines.append("情緒相較前一日變化有限，短期風險基調大致延續。")

    if len(samples) >= 3:
        recent_topics = [item["top_topic"] for item in samples[:3]]
        distinct_topics = len(set(recent_topics))
        if distinct_topics == 1:
            lines.append(f"近三日主趨勢一致為 {recent_topics[0]}，代表短期主線已形成。")
        else:
            lines.append(f"近三日出現 {distinct_topics} 種主趨勢，代表市場仍處在重新定價與重新排序階段。")

    return lines


def _build_time_comparison(
    current_trends: list[dict[str, str]],
    sentiment: dict[str, float | str | int],
    samples: list[dict[str, str]],
) -> list[str]:
    if not samples:
        return ["尚無歷史觀察可比較，先把今天作為基準日。"]

    latest_previous = samples[0]
    lines = [
        (
            f"相較 {latest_previous['observed_date']}，主趨勢"
            f"{'維持' if latest_previous['top_topic'] == (current_trends[0]['bucket'] if current_trends else 'general') else '轉換為'}"
            f" {_topic_name(current_trends[0]['bucket'] if current_trends else 'general')}。"
        )
    ]

    sentiment_delta = round(float(sentiment["score"]) - float(latest_previous["sentiment_score"]), 3)
    if sentiment_delta > 0.15:
        lines.append(f"情緒較昨日回升 {sentiment_delta}，風險偏好有些修復。")
    elif sentiment_delta < -0.15:
        lines.append(f"情緒較昨日再走弱 {abs(sentiment_delta)}，今天結論應更保守。")
    else:
        lines.append("情緒相較昨日變化有限，建議沿用前一日的驗證框架。")

    if len(samples) >= 3:
        avg_prev_sentiment = round(sum(float(item["sentiment_score"]) for item in samples[:3]) / 3, 3)
        drift = round(float(sentiment["score"]) - avg_prev_sentiment, 3)
        direction = "高於" if drift >= 0 else "低於"
        lines.append(f"今日情緒指數 {direction} 近三日均值 {abs(drift)}，可用來判斷是短暫波動還是持續偏移。")

    return lines


def _build_source_profile(news: list[dict[str, str]]) -> dict[str, object]:
    source_counter = Counter(str(item.get("source") or "未知來源") for item in news)
    total = len(news) or 1
    top_source, top_count = source_counter.most_common(1)[0] if source_counter else ("未知來源", 0)
    concentration = round(top_count / total, 3)
    return {
        "unique_sources": len(source_counter),
        "top_source": top_source,
        "top_source_ratio": concentration,
        "source_counts": source_counter,
    }


def _build_confidence_summary(
    news: list[dict[str, str]],
    trends: list[dict[str, str]],
    source_profile: dict[str, object],
) -> dict[str, object]:
    top_bucket = trends[0]["bucket"] if trends else "general"
    unique_sources = int(source_profile["unique_sources"])
    top_source_ratio = float(source_profile["top_source_ratio"])

    score = 40
    if len(news) >= 8:
        score += 15
    if unique_sources >= 3:
        score += 20
    elif unique_sources == 2:
        score += 10
    if top_source_ratio <= 0.5:
        score += 15
    elif top_source_ratio >= 0.8:
        score -= 10
    if any(item.get("bucket") == top_bucket for item in trends[:3]):
        score += 10

    score = max(0, min(100, score))
    if score >= 80:
        label = "高"
    elif score >= 60:
        label = "中"
    else:
        label = "保守"

    reasons = [
        f"新聞樣本 {len(news)} 則",
        f"來源 {unique_sources} 個",
        f"最高集中來源 {source_profile['top_source']} 佔比 {top_source_ratio:.0%}",
        f"主趨勢 {_topic_name(top_bucket)} 位於趨勢榜首",
    ]
    return {"score": score, "label": label, "reasons": reasons}


def _focus_confidence_label(score: int) -> str:
    if score >= 75:
        return "高"
    if score >= 55:
        return "中"
    return "保守"


def _focus_rationale(item: dict[str, str], impacts: list[str]) -> str:
    event_type = _classify_event_type(item)
    if event_type == "地緣政治":
        return "事件本身帶有安全外溢風險，需觀察是否推高能源、物流或政策反應。"
    if event_type == "政策監管":
        return "重點不只是事件本身，而是執法尺度是否改變平台、產業或市場邊界。"
    if event_type == "產業科技":
        return "應追蹤能力敘事是否轉成部署速度、成本壓力與治理責任。"
    if event_type == "市場供應":
        return "要確認價格訊號是否已開始往供應鏈、企業成本與消費端傳導。"
    if "社會信任" in impacts:
        return "需注意這類事件是否改變社會信任與公共討論的穩定度。"
    return "先觀察事件是否從單點新聞升級成跨領域傳導。"


def _score_focus_item(item: dict[str, str], top_bucket: str) -> int:
    score = 40
    impacts = _infer_second_order_tags(item)
    event_type = _classify_event_type(item)
    if top_bucket in {"general", "economy"} and any(tag in impacts for tag in {"價格壓力", "供應鏈", "政策反應"}):
        score += 20
    if top_bucket in {"ai", "technology"} and event_type == "產業科技":
        score += 20
    if event_type in {"地緣政治", "政策監管"}:
        score += 15
    if len(impacts) >= 2:
        score += 10
    title = str(item.get("title") or "").lower()
    if any(token in title for token in ["war", "attack", "tariff", "ai", "market", "policy"]):
        score += 10
    return min(score, 95)


def _build_focus_event_cards(news: list[dict[str, str]], trends: list[dict[str, str]]) -> list[dict[str, object]]:
    top_bucket = trends[0]["bucket"] if trends else "general"
    cards: list[dict[str, object]] = []
    for item in news:
        impacts = _infer_second_order_tags(item)
        score = _score_focus_item(item, top_bucket)
        cards.append(
            {
                "title": item["title"],
                "link": item["link"],
                "source": item["source"],
                "topic": item["topic"],
                "published_at": item["published_at"],
                "summary": item["summary"],
                "event_type": _classify_event_type(item),
                "impacts": impacts,
                "confidence_score": score,
                "confidence_label": _focus_confidence_label(score),
                "rationale": _focus_rationale(item, impacts),
            }
        )

    cards.sort(key=lambda item: int(item["confidence_score"]), reverse=True)
    return cards[:3]


def _build_key_takeaways(
    news: list[dict[str, str]],
    trends: list[dict[str, str]],
    sentiment: dict[str, float | str | int],
) -> list[str]:
    top_trend, second_trend = _top_topic_pair(trends)
    focus_event = _build_focus_event_cards(news, trends)
    newest_news = focus_event[0]["title"] if focus_event else "今日沒有可用新聞樣本。"

    return [
        (
            f"全球焦點維持在 {_topic_name(top_trend['bucket'])}（{top_trend['metric_value']}%），"
            f"次軸為 {_topic_name(second_trend['bucket'])}（{second_trend['metric_value']}%）。"
        ),
        (
            f"社會情緒指數 {sentiment['score']}（{sentiment['label']}），"
            f"正負訊號比為 {_format_ratio(int(sentiment['positive_hits']), int(sentiment['negative_hits']))}。"
        ),
        f"今日代表事件：{newest_news}。建議把它放進事件鏈，而不是單看單則新聞。",
    ]


def _build_personal_notes(
    trends: list[dict[str, str]],
    philosophy: list[dict[str, str]],
    sentiment: dict[str, float | str | int],
) -> list[str]:
    top_topic = _topic_name(trends[0]["bucket"] if trends else "general")
    philosophy_focus = philosophy[0] if philosophy else {"title": "Unknown", "author": "Unknown"}

    return [
        (
            f"若 {top_topic} 是時代主題，當前決策最容易忽略的是長期外部性；"
            "需要在效率、風險與責任之間設下可驗證的邊界。"
        ),
        (
            f"情緒為 {sentiment['label']} 時，判斷更容易被敘事帶動；"
            "先驗證資料與影響鏈，再形成立場。"
        ),
        (
            f"以 {philosophy_focus['author']}《{philosophy_focus['title']}》作為反思鏡："
            "今天的行動是否能長期成立，而且不依賴短期情緒。"
        ),
    ]


def _build_knowledge_links(
    trends: list[dict[str, str]],
    philosophy: list[dict[str, str]],
    notes: list[str],
) -> list[dict[str, str]]:
    top_topic = _topic_name(trends[0]["bucket"] if trends else "general")
    second_topic = _topic_name(trends[1]["bucket"] if len(trends) > 1 else "general")

    first_philosophy = philosophy[0] if philosophy else {"title": "Ethics", "author": "Unknown"}
    second_philosophy = philosophy[1] if len(philosophy) > 1 else first_philosophy

    return [
        {
            "from": f"Trend:{top_topic}",
            "to": f"Philosophy:{first_philosophy['title']}",
            "reason": "主趨勢需要對應的倫理框架與判準，避免只有速度沒有方向。",
        },
        {
            "from": f"Trend:{second_topic}",
            "to": f"Philosophy:{second_philosophy['title']}",
            "reason": "次趨勢可作為對照軸，檢查主敘事是否站得住腳。",
        },
        {
            "from": f"Philosophy:{first_philosophy['author']}",
            "to": "Note:邊界與責任",
            "reason": notes[0],
        },
        {
            "from": "Sentiment:社會情緒",
            "to": "Note:先驗證再立場",
            "reason": notes[1],
        },
    ]


def _build_trend_intersections(trends: list[dict[str, str]]) -> list[str]:
    top_trend, second_trend = _top_topic_pair(trends)
    intersections = [
        (
            f"{_topic_name(top_trend['bucket'])} 與 {_topic_name(second_trend['bucket'])} 高度接近，"
            "代表主敘事尚未完全收斂，短期內容易被單一事件重新排序。"
        )
    ]

    buckets = {item["bucket"] for item in trends[:5]}
    if "policy" in buckets and "security" in buckets:
        intersections.append("政策與安全同時出現，代表治理議題正在從討論層走向執行層。")
    if "economy" in buckets:
        intersections.append("經濟信號仍在榜內，建議把市場波動當成科技與地緣事件的放大器。")
    return intersections


def _build_action_items(
    news: list[dict[str, str]],
    trends: list[dict[str, str]],
    sentiment: dict[str, float | str | int],
    focus_items: list[dict[str, object]],
    source_profile: dict[str, object],
) -> list[str]:
    actions: list[str] = []
    top_bucket = trends[0]["bucket"] if trends else "general"
    focus = focus_items[0] if focus_items else None
    if focus:
        actions.append(
            f"先追蹤頭條〈{focus['title']}〉，重點放在 {focus['rationale'].replace('。', '')}。"
        )
    if top_bucket in TOPIC_EVENT_HINTS:
        _, hint = TOPIC_EVENT_HINTS[top_bucket]
        actions.append(f"今日主線偏向 {_topic_name(top_bucket)}，優先驗證 {hint}。")
    if float(sentiment["score"]) <= -0.2:
        actions.append("負面情緒偏高，今天的結論先以風險盤點為主，不急著下方向判斷。")
    if float(source_profile["top_source_ratio"]) >= 0.7:
        actions.append(
            f"目前樣本有 {float(source_profile['top_source_ratio']):.0%} 來自 {source_profile['top_source']}，請補找第二來源再下結論。"
        )
    elif news:
        actions.append(f"優先複查頭條〈{news[0]['title']}〉的後續更新與來源一致性。")
    return actions[:4]


def _build_watch_items(news: list[dict[str, str]], focus_items: list[dict[str, object]]) -> list[str]:
    label_sources: dict[str, set[str]] = {}
    for item in news:
        source = str(item.get("source") or "未知來源")
        for label in _infer_second_order_tags(item):
            label_sources.setdefault(label, set()).add(source)

    if not label_sources:
        return ["今日樣本沒有明顯集中風險，維持常規監測。"]

    lines: list[str] = []
    for label, sources in sorted(label_sources.items(), key=lambda pair: len(pair[1]), reverse=True)[:3]:
        lines.append(f"關注 {label} 是否從目前的 {len(sources)} 個來源，擴散成更廣泛共識。")

    for item in focus_items[:1]:
        lines.append(f"追蹤〈{item['title']}〉是否在 24 小時內出現政策回應、價格變化或更多交叉報導。")
    return lines[:4]


def _sanitize_id(text: str) -> str:
    chars = [ch.lower() if ch.isalnum() else "_" for ch in text]
    cleaned = "".join(chars)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "node"


def _write_thought_links_report(date_label: str, links: list[dict[str, str]]) -> str:
    path = REPORT_DIR / f"thought_links_{date_label}.md"

    nodes: list[str] = []
    for link in links:
        nodes.append(link["from"])
        nodes.append(link["to"])

    unique_nodes = list(dict.fromkeys(nodes))

    lines: list[str] = []
    lines.append(f"# 影月系統思想連結 ({date_label})")
    lines.append("")
    lines.append("## 節點清單")
    for node in unique_nodes:
        lines.append(f"- {node}")
    lines.append("")

    lines.append("## 關係說明")
    for idx, link in enumerate(links, start=1):
        lines.append(f"{idx}. {link['from']} -> {link['to']}：{link['reason']}")
    lines.append("")

    lines.append("## Mermaid")
    lines.append("```mermaid")
    lines.append("graph LR")
    for node in unique_nodes:
        node_id = _sanitize_id(node)
        lines.append(f'  {node_id}["{node}"]')
    for link in links:
        src = _sanitize_id(link["from"])
        dst = _sanitize_id(link["to"])
        lines.append(f"  {src} --> {dst}")
    lines.append("```")

    path.write_text("\n".join(lines), encoding="utf-8-sig")
    return str(path)


def _upsert_observation_log(
    date_label: str,
    sentiment: dict[str, float | str | int],
    trends: list[dict[str, str]],
    takeaways: list[str],
) -> None:
    top_topic = trends[0]["bucket"] if trends else "general"
    second_topic = trends[1]["bucket"] if len(trends) > 1 else "general"

    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO observation_logs (
                observed_date,
                sentiment_score,
                sentiment_label,
                top_topic,
                second_topic,
                key_takeaway
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(observed_date) DO UPDATE SET
                sentiment_score = excluded.sentiment_score,
                sentiment_label = excluded.sentiment_label,
                top_topic = excluded.top_topic,
                second_topic = excluded.second_topic,
                key_takeaway = excluded.key_takeaway
            """,
            (
                date_label,
                sentiment["score"],
                sentiment["label"],
                top_topic,
                second_topic,
                takeaways[0],
            ),
        )
        conn.commit()


def _write_weekly_observation_report(date_label: str) -> str:
    week_key = datetime.fromisoformat(date_label).isocalendar()
    week_label = f"{week_key.year}-W{week_key.week:02d}"

    with db_connection() as conn:
        rows = conn.execute(
            """
            SELECT observed_date, sentiment_score, sentiment_label, top_topic, second_topic, key_takeaway
            FROM observation_logs
            ORDER BY observed_date DESC
            LIMIT 7
            """
        ).fetchall()

    samples = [dict(r) for r in rows]
    path = REPORT_DIR / f"weekly_observation_{week_label}.md"

    lines: list[str] = []
    lines.append(f"# 影月系統每週觀察 ({week_label})")
    lines.append("")

    if not samples:
        lines.append("本週尚無觀察資料。")
        path.write_text("\n".join(lines), encoding="utf-8-sig")
        return str(path)

    avg_sentiment = round(sum(float(item["sentiment_score"]) for item in samples) / len(samples), 3)
    topic_counter = Counter(item["top_topic"] for item in samples)
    top_topic, top_count = topic_counter.most_common(1)[0]

    lines.append(f"- 覆蓋天數: {len(samples)}")
    lines.append(f"- 平均情緒指數: {avg_sentiment}（{_label_sentiment(avg_sentiment)}）")
    lines.append(f"- 本週主趨勢: {_topic_name(top_topic)}（{top_count} 天）")
    lines.append("")

    lines.append("## 每週觀察")
    lines.append("1. 世界新聞仍圍繞主趨勢展開，建議維持主線追蹤，同時監測次要議題是否轉強。")
    lines.append("2. 情緒只能作為風險濾鏡，不應直接取代事實判斷；情緒偏移時要提高驗證標準。")
    lines.append("3. 若政策、安全與經濟交錯出現，代表事件已經開始從敘事進入影響傳導。")
    lines.append("")

    lines.append("## 思想連結（週摘要）")
    for idx, item in enumerate(reversed(samples), start=1):
        lines.append(
            f"{idx}. {item['observed_date']} | {_topic_name(item['top_topic'])} -> {_topic_name(item['second_topic'])} | {item['key_takeaway']}"
        )

    path.write_text("\n".join(lines), encoding="utf-8-sig")
    return str(path)


def generate_daily_report(report_date: str | None = None) -> dict[str, str]:
    now = datetime.now().astimezone()
    date_label = report_date or now.date().isoformat()

    news = _fetch_news(limit=10)
    trends = _fetch_trends()
    philosophy = _fetch_philosophy(limit=3)

    sentiment = _analyze_sentiment(news)
    tech_signals = _analyze_tech_signals(news)
    takeaways = _build_key_takeaways(news, trends, sentiment)
    notes = _build_personal_notes(trends, philosophy, sentiment)
    links = _build_knowledge_links(trends, philosophy, notes)
    intersections = _build_trend_intersections(trends)
    source_profile = _build_source_profile(news)
    confidence = _build_confidence_summary(news, trends, source_profile)
    focus_items = _build_focus_event_cards(news, trends)
    second_order_impacts = _build_second_order_impact_lines(news)

    _upsert_observation_log(date_label, sentiment, trends, takeaways)
    recent_observations = _fetch_recent_observations(limit=4)
    trend_pulse = _build_trend_pulse(recent_observations[:3])
    time_comparison = _build_time_comparison(trends, sentiment, recent_observations[1:])
    actions = _build_action_items(news, trends, sentiment, focus_items, source_profile)
    watch_items = _build_watch_items(news, focus_items)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORT_DIR / f"daily_report_{date_label}.md"
    csv_path = REPORT_DIR / f"daily_report_{date_label}_news.csv"

    lines: list[str] = []
    lines.append(f"# 影月系統每日觀察 ({date_label})")
    lines.append("")
    lines.append(f"- 生成時間 (Local): {now.isoformat()}")
    lines.append(f"- 新聞筆數: {len(news)}")
    lines.append(f"- 趨勢指標數: {len(trends)}")
    lines.append(f"- 來源數: {source_profile['unique_sources']}（最高集中來源 {source_profile['top_source']} / {float(source_profile['top_source_ratio']):.0%}）")
    lines.append(f"- 判讀信心: {confidence['label']} / {confidence['score']}")
    lines.append("")

    lines.append("## 每日觀察")
    for i, item in enumerate(takeaways, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 近三日趨勢脈動")
    for i, item in enumerate(trend_pulse, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 與昨日/近三日比較")
    for i, item in enumerate(time_comparison, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 趨勢交界")
    for i, item in enumerate(intersections, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## Top 3 關鍵事件")
    for idx, item in enumerate(focus_items, start=1):
        lines.append(f"{idx}. [{item['title']}]({item['link']})")
        lines.append(
            f"   - 類型: {item['event_type']} | 信心: {item['confidence_label']} ({item['confidence_score']}) | 來源: {item['source']}"
        )
        lines.append(f"   - 事件摘要: {item['summary']}")
        lines.append(f"   - 二階影響: {'、'.join(item['impacts'])}")
        lines.append(f"   - 判讀依據: {item['rationale']}")
    if not focus_items:
        lines.append("1. 今日沒有足夠樣本可抽出關鍵事件。")
    lines.append("")

    lines.append("## 判讀信心與資料品質")
    lines.append(f"1. 今日整體判讀信心為 {confidence['label']}（{confidence['score']} / 100）。")
    for idx, reason in enumerate(confidence["reasons"], start=2):
        lines.append(f"{idx}. {reason}")
    if float(source_profile["top_source_ratio"]) >= 0.7:
        lines.append(f"{len(confidence['reasons']) + 2}. 單一來源集中度偏高，今天的結論應以保守解讀為主。")
    lines.append("")

    lines.append("## 二階影響標籤")
    for i, item in enumerate(second_order_impacts, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 今日可執行")
    for i, item in enumerate(actions, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 需要持續觀察")
    for i, item in enumerate(watch_items, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 其餘新聞樣本")
    focus_titles = {str(item["title"]) for item in focus_items}
    remaining_news = [item for item in news if item["title"] not in focus_titles]
    for idx, item in enumerate(remaining_news or news, start=1):
        lines.append(f"{idx}. [{item['title']}]({item['link']})")
        lines.append(
            f"   - 來源: {item['source']} | 主題: {_topic_name(item['topic'])} | 類型: {_classify_event_type(item)} | 時間: {item['published_at']}"
        )
        lines.append(f"   - 摘要: {item['summary']}")
        lines.append(f"   - 二階影響: {'、'.join(_infer_second_order_tags(item))}")
    lines.append("")

    lines.append("## 社會情緒觀察")
    lines.append(f"- 情緒指數: {sentiment['score']}（{sentiment['label']}）")
    lines.append(f"- 正向訊號: {sentiment['positive_hits']}")
    lines.append(f"- 負向訊號: {sentiment['negative_hits']}")
    lines.append("")

    lines.append("## 科技趨勢分析")
    for trend in trends[:5]:
        lines.append(f"- 趨勢占比 | {_topic_name(trend['bucket'])}: {trend['metric_value']}%")
    lines.append("- 技術訊號強度:")
    for signal, score in tech_signals:
        lines.append(f"  - {signal}: {score}")
    lines.append("")

    lines.append("## 個人思想筆記")
    for i, note in enumerate(notes, start=1):
        lines.append(f"{i}. {note}")
    lines.append("")

    lines.append("## 知識圖譜連結")
    for i, link in enumerate(links, start=1):
        lines.append(f"{i}. {link['from']} -> {link['to']}：{link['reason']}")
    lines.append("")

    lines.append("## 哲學參照")
    for entry in philosophy:
        lines.append(f"- {entry['title']} ({entry['author']})")
        lines.append(f"  - 流派/時代: {entry['school']} / {entry['era']}")
        lines.append(f"  - 摘要: {entry['summary']}")
        lines.append(f"  - 關鍵詞: {entry['keywords']}")

    md_path.write_text("\n".join(lines), encoding="utf-8-sig")

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["title", "source", "topic", "published_at", "summary", "link"],
        )
        writer.writeheader()
        writer.writerows(news)

    thought_links_path = _write_thought_links_report(date_label, links)
    weekly_path = _write_weekly_observation_report(date_label)

    return {
        "date": date_label,
        "markdown_report": str(md_path),
        "news_csv": str(csv_path),
        "weekly_observation": weekly_path,
        "thought_links": thought_links_path,
    }

