from __future__ import annotations

import csv
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
    "供應鏈": ["supply", "ship", "factory", "export", "shortage", "cocoa", "oil"],
    "價格壓力": ["price", "prices", "inflation", "cost", "market", "shares"],
    "政策反應": ["law", "policy", "regulation", "amnesty", "licence", "verify"],
    "安全風險": ["war", "attack", "terror", "gunfire", "explosion", "security"],
    "社會信任": ["public", "broadcaster", "election", "embassy", "police"],
    "平台治理": ["ai", "platform", "porn", "monitor", "var", "online"],
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


def _top_topic_pair(trends: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, str]]:
    top_trend = trends[0] if trends else {"bucket": "general", "metric_value": 0}
    second_trend = trends[1] if len(trends) > 1 else {"bucket": "general", "metric_value": 0}
    return top_trend, second_trend


def _infer_second_order_tags(item: dict[str, str]) -> list[str]:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    tags = [label for label, keywords in SECOND_ORDER_IMPACT_RULES.items() if any(token in text for token in keywords)]
    if not tags:
        topic = str(item.get("topic") or "general")
        if topic == "technology":
            tags = ["平台治理"]
        elif topic == "world":
            tags = ["社會信任"]
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


def _build_key_takeaways(
    news: list[dict[str, str]],
    trends: list[dict[str, str]],
    sentiment: dict[str, float | str | int],
) -> list[str]:
    top_trend, second_trend = _top_topic_pair(trends)
    newest_news = news[0]["title"] if news else "今日沒有可用新聞樣本。"

    return [
        (
            f"全球焦點維持在 {top_trend['bucket']}（{top_trend['metric_value']}%），"
            f"次軸為 {second_trend['bucket']}（{second_trend['metric_value']}%）。"
        ),
        (
            f"社會情緒指數 {sentiment['score']}（{sentiment['label']}），"
            f"正負訊號比為 {_format_ratio(int(sentiment['positive_hits']), int(sentiment['negative_hits']))}。"
        ),
        f"今日代表事件：{newest_news}。建議用事件鏈方式追蹤其二階影響。",
    ]


def _build_personal_notes(
    trends: list[dict[str, str]],
    philosophy: list[dict[str, str]],
    sentiment: dict[str, float | str | int],
) -> list[str]:
    top_topic = trends[0]["bucket"] if trends else "general"
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
    top_topic = trends[0]["bucket"] if trends else "general"
    second_topic = trends[1]["bucket"] if len(trends) > 1 else "general"

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
) -> list[str]:
    actions: list[str] = []
    top_bucket = trends[0]["bucket"] if trends else "general"
    if top_bucket in {"general", "economy"}:
        actions.append("把頭條事件拆成供應、價格、政策回應三段，觀察是否開始互相傳導。")
    if top_bucket == "ai":
        actions.append("追蹤 AI 敘事是否從模型能力轉向部署、成本或治理限制。")
    if float(sentiment["score"]) <= -0.2:
        actions.append("負面情緒偏高，今天的結論先以風險盤點為主，不急著下方向判斷。")
    if news:
        actions.append(f"優先複查頭條〈{news[0]['title']}〉的後續更新與來源一致性。")
    return actions[:4]


def _build_watch_items(news: list[dict[str, str]]) -> list[str]:
    keywords = {
        "war": "地緣衝突",
        "attack": "安全事件",
        "inflation": "通膨壓力",
        "oil": "能源價格",
        "policy": "政策變動",
        "ai": "AI 熱點",
    }
    hits: list[str] = []
    for item in news:
        text = f"{item['title']} {item['summary']}".lower()
        for token, label in keywords.items():
            if token in text and label not in hits:
                hits.append(label)
    if not hits:
        return ["今日樣本沒有明顯集中風險，維持常規監測。"]
    return [f"關注 {label} 是否持續擴散到更多新聞來源。" for label in hits[:4]]


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
    lines.append(f"- 本週主趨勢: {top_topic}（{top_count} 天）")
    lines.append("")

    lines.append("## 每週觀察")
    lines.append("1. 世界新聞仍圍繞主趨勢展開，建議維持主線追蹤，同時監測次要議題是否轉強。")
    lines.append("2. 情緒只能作為風險濾鏡，不應直接取代事實判斷；情緒偏移時要提高驗證標準。")
    lines.append("3. 若政策、安全與經濟交錯出現，代表事件已經開始從敘事進入影響傳導。")
    lines.append("")

    lines.append("## 思想連結（週摘要）")
    for idx, item in enumerate(reversed(samples), start=1):
        lines.append(
            f"{idx}. {item['observed_date']} | {item['top_topic']} -> {item['second_topic']} | {item['key_takeaway']}"
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
    actions = _build_action_items(news, trends, sentiment)
    watch_items = _build_watch_items(news)
    second_order_impacts = _build_second_order_impact_lines(news)

    _upsert_observation_log(date_label, sentiment, trends, takeaways)
    trend_pulse = _build_trend_pulse(_fetch_recent_observations(limit=3))

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = REPORT_DIR / f"daily_report_{date_label}.md"
    csv_path = REPORT_DIR / f"daily_report_{date_label}_news.csv"

    lines: list[str] = []
    lines.append(f"# 影月系統每日觀察 ({date_label})")
    lines.append("")
    lines.append(f"- 生成時間 (Local): {now.isoformat()}")
    lines.append(f"- 新聞筆數: {len(news)}")
    lines.append(f"- 趨勢指標數: {len(trends)}")
    lines.append("")

    lines.append("## 每日觀察")
    for i, item in enumerate(takeaways, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 近三日趨勢脈動")
    for i, item in enumerate(trend_pulse, start=1):
        lines.append(f"{i}. {item}")
    lines.append("")

    lines.append("## 趨勢交界")
    for i, item in enumerate(intersections, start=1):
        lines.append(f"{i}. {item}")
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

    lines.append("## 世界新聞整理")
    for idx, item in enumerate(news, start=1):
        lines.append(f"{idx}. [{item['title']}]({item['link']})")
        lines.append(f"   - 來源: {item['source']} | 主題: {item['topic']} | 時間: {item['published_at']}")
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
        lines.append(f"- 趨勢占比 | {trend['bucket']}: {trend['metric_value']}%")
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

