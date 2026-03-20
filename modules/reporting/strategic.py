from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

TOPIC_LABELS = {
    "ai": "AI",
    "general": "綜合",
    "policy": "政策",
    "security": "安全",
    "economy": "經濟",
    "technology": "科技",
    "world": "世界",
    "politics": "政治",
    "society": "社會",
    "culture": "文化",
}

CATEGORY_RULES = {
    "economy": {
        "include": ("oil", "inflation", "price", "prices", "market", "tariff", "trade", "ship", "supply", "factory"),
        "exclude": ("prize", "supermarket"),
    },
    "technology": {
        "include": ("ai", "model", "chip", "semiconductor", "platform", "software", "data", "digital", "compute"),
        "exclude": ("aid",),
    },
    "politics": {
        "include": ("war", "attack", "leader", "election", "embassy", "police", "government", "policy", "terror", "strike"),
        "exclude": ("policy debate show",),
    },
    "society": {
        "include": ("court", "compensation", "rights", "protest", "public", "family", "school", "hospital"),
        "exclude": (),
    },
    "culture": {
        "include": ("oscars", "football", "world cup", "film", "award", "sport", "festival"),
        "exclude": (),
    },
}
CITY_KEYWORDS = {
    "交通與物流": ("oil", "ship", "transport", "flight", "traffic", "delivery"),
    "能源與公共成本": ("oil", "energy", "power", "electricity", "price", "inflation"),
    "數位治理與服務摩擦": ("ai", "online", "verify", "platform", "data", "security"),
    "公共安全與社會信任": ("attack", "police", "gunfire", "terror", "embassy", "war"),
}
SYSTEM_KEYWORDS = {
    "供應鏈與價格傳導": ("oil", "ship", "supply", "market", "trade", "price"),
    "政策與監管邊界": ("policy", "government", "verify", "law", "tariff", "amnesty"),
    "平台治理與責任分配": ("ai", "platform", "online", "data", "security"),
    "安全風險與制度韌性": ("war", "attack", "terror", "embassy", "police"),
}

FOCUS_AREA_HINTS = {
    "economy": "先確認是否改變價格、供應鏈或企業成本。",
    "technology": "先確認是否改變部署節奏、成本結構或治理責任。",
    "politics": "先確認是否擴散成政策、外交或安全層級的後續反應。",
    "society": "先確認是否影響社會信任、公共服務或制度正當性。",
    "culture": "先確認是否只是話題事件，或已外溢到公共討論與城市運作。",
}


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _topic_name(bucket: str) -> str:
    return TOPIC_LABELS.get(bucket, bucket)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(_contains_term(lowered, term) for term in terms)


def _matches_rule(text: str, include: tuple[str, ...], exclude: tuple[str, ...]) -> int:
    if any(_contains_term(text, term) for term in exclude):
        return 0
    return sum(1 for term in include if _contains_term(text, term))


def _format_percent(value: object) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def _classify_item(item: dict[str, str]) -> str:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    scores = {
        label: _matches_rule(text, rule["include"], rule["exclude"])
        for label, rule in CATEGORY_RULES.items()
    }
    category, score = max(scores.items(), key=lambda pair: pair[1])
    if score == 0:
        topic = str(item.get("topic") or "")
        if topic in {"ai", "technology"}:
            return "technology"
        if topic in {"economy"}:
            return "economy"
        if topic in {"world"}:
            return "society"
        return "politics"
    return category


def _pick_signals(news: list[dict[str, str]], mapping: dict[str, tuple[str, ...]], fallback: str) -> list[str]:
    counter: Counter[str] = Counter()
    for item in news:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        for label, keywords in mapping.items():
            if any(token in text for token in keywords):
                counter[label] += 1
    if not counter:
        return [fallback]
    return [name for name, _ in counter.most_common(3)]


def _line_from_observation(observation: dict[str, object]) -> str:
    return (
        f"{observation['observed_date']}：主趨勢 {_topic_name(str(observation['top_topic']))}，"
        f"次軸 {_topic_name(str(observation['second_topic']))}，情緒 {observation['sentiment_label']}。"
    )


def _source_profile(news: list[dict[str, str]]) -> tuple[int, str, float]:
    counter = Counter(str(item.get("source") or "未知來源") for item in news)
    if not counter:
        return 0, "未知來源", 0.0
    top_source, top_count = counter.most_common(1)[0]
    return len(counter), top_source, round(top_count / len(news), 3)


def build_strategic_weekly_report(
    week_label: str,
    generated_at: str,
    observations: list[dict[str, object]],
    trends: list[dict[str, object]],
    news: list[dict[str, str]],
) -> str:
    avg_sentiment = 0.0
    if observations:
        avg_sentiment = round(sum(float(item["sentiment_score"]) for item in observations) / len(observations), 3)

    top_trend = trends[0] if trends else {"bucket": "general", "metric_value": 0}
    second_trend = trends[1] if len(trends) > 1 else {"bucket": "general", "metric_value": 0}
    top_topic_counts = Counter(item.get("top_topic", "general") for item in observations)
    dominant_topic = top_topic_counts.most_common(1)[0][0] if top_topic_counts else str(top_trend.get("bucket", "general"))

    categories = {"economy": [], "technology": [], "politics": []}
    for item in news:
        category = _classify_item(item)
        if category not in categories:
            continue
        categories[category].append(item)

    city_signals = _pick_signals(news, CITY_KEYWORDS, "城市層訊號仍分散，先追蹤價格、物流與數位服務摩擦。")
    system_signals = _pick_signals(news, SYSTEM_KEYWORDS, "系統層訊號仍分散，先追蹤制度邊界與供應鏈傳導。")
    unique_sources, top_source, top_source_ratio = _source_profile(news)

    summary_lines = [
        (
            f"本週主線仍由 {_topic_name(dominant_topic)} 帶動；最新趨勢指標以 {_topic_name(str(top_trend.get('bucket', 'general')))} "
            f"({_format_percent(top_trend.get('metric_value'))}) 領先，次軸為 {_topic_name(str(second_trend.get('bucket', 'general')))} "
            f"({_format_percent(second_trend.get('metric_value'))})。"
        ),
        (
            f"近 {len(observations)} 天平均情緒指數為 {avg_sentiment}，顯示觀察樣本的風險基調"
            f"{'偏緊' if avg_sentiment <= -0.2 else '相對中性'}。"
        ),
        (
            f"城市層面建議優先追蹤 {'、'.join(city_signals)}；系統層面則聚焦 {'、'.join(system_signals)}。"
        ),
        (
            f"本週樣本共 {unique_sources} 個來源；其中 {top_source} 佔比 {top_source_ratio:.0%}，"
            f"{'可作為交叉驗證基礎' if top_source_ratio < 0.7 else '仍需補更多交叉來源'}。"
        ),
    ]

    focus_items = news[:5]
    lines: list[str] = []
    lines.append(f"# 影月系統策略週報 ({week_label})")
    lines.append("")
    lines.append(f"- 生成時間: {generated_at}")
    lines.append(f"- 覆蓋觀察天數: {len(observations)}")
    lines.append(f"- 納入新聞樣本: {len(news)}")
    lines.append(f"- 來源概況: {unique_sources} 個來源，最高集中 {top_source} / {top_source_ratio:.0%}")
    lines.append("")

    lines.append("## 摘要")
    for idx, item in enumerate(summary_lines, start=1):
        lines.append(f"{idx}. {item}")
    lines.append("")

    lines.append("## 一、主線判讀")
    lines.append(
        f"1. 經濟面：本週經濟訊號主要圍繞 {('、'.join(entry['title'] for entry in categories['economy'][:2])) if categories['economy'] else '價格與供應鏈訊號仍偏分散'}。"
    )
    lines.append(
        f"2. 科技面：本週科技訊號主要圍繞 {('、'.join(entry['title'] for entry in categories['technology'][:2])) if categories['technology'] else 'AI、平台與數位治理訊號交錯'}。"
    )
    lines.append(
        f"3. 政治面：本週政治與安全訊號主要圍繞 {('、'.join(entry['title'] for entry in categories['politics'][:2])) if categories['politics'] else '安全與政策風險持續交錯'}。"
    )
    lines.append("")

    lines.append("## 二、城市與系統傳導")
    lines.append(f"1. 城市運作：本週最需要注意的城市層影響為 {'、'.join(city_signals)}。")
    lines.append(f"2. 系統層面：本週最需要注意的系統層影響為 {'、'.join(system_signals)}。")
    lines.append(
        "3. 判讀原則：若價格、政策與安全訊號同時出現，代表事件已開始從單點新聞轉成跨部門傳導。"
    )
    lines.append("")

    lines.append("## 三、焦點事件")
    if not focus_items:
        lines.append("本週尚無足夠新聞樣本。")
    for idx, item in enumerate(focus_items, start=1):
        category = _classify_item(item)
        lines.append(f"{idx}. {item['title']}")
        lines.append(f"   - 類別: {_topic_name(category)} | 來源: {item['source']} | 主題: {_topic_name(item['topic'])}")
        lines.append(f"   - 事件摘要: {item['summary']}")
        city_impact = next((label for label, terms in CITY_KEYWORDS.items() if _contains_any(f"{item['title']} {item['summary']}", terms)), "公共感受與服務穩定度")
        system_impact = next((label for label, terms in SYSTEM_KEYWORDS.items() if _contains_any(f"{item['title']} {item['summary']}", terms)), "制度邊界與跨部門傳導")
        lines.append(f"   - 影響對象: 城市面關注 {city_impact}；系統面關注 {system_impact}")
        lines.append(f"   - 傳導路徑: {FOCUS_AREA_HINTS.get(category, '先確認是否已從新聞敘事轉為制度或成本傳導。')}")
        lines.append("   - 觀察指標: 來源數量、是否出現政策回應、是否轉成價格/物流/公共安全訊號")
    lines.append("")

    lines.append("## 四、近一週觀察軌跡")
    if observations:
        for idx, observation in enumerate(reversed(observations), start=1):
            lines.append(f"{idx}. {_line_from_observation(observation)}")
    else:
        lines.append("1. 本週尚無 observation_logs 可供彙整。")
    lines.append("")

    lines.append("## 五、下週觀察清單")
    watch_items = [
        f"追蹤 {_topic_name(str(top_trend.get('bucket', 'general')))} 是否持續領先，或被 {_topic_name(str(second_trend.get('bucket', 'general')))} 取代。",
        f"持續觀察 {'、'.join(city_signals)} 是否從新聞敘事變成城市營運成本。",
        f"持續觀察 {'、'.join(system_signals)} 是否從討論階段走向制度化。",
    ]
    for idx, item in enumerate(watch_items, start=1):
        lines.append(f"{idx}. {item}")
    lines.append("")

    lines.append("## 六、固定輸出摘要")
    lines.append(f"- Dominant topic: {_topic_name(dominant_topic)}")
    lines.append(f"- Top trend: {_topic_name(str(top_trend.get('bucket', 'general')))} / {_format_percent(top_trend.get('metric_value'))}")
    lines.append(f"- Second trend: {_topic_name(str(second_trend.get('bucket', 'general')))} / {_format_percent(second_trend.get('metric_value'))}")
    lines.append(f"- Avg sentiment: {avg_sentiment}")
    lines.append(f"- City signals: {'、'.join(city_signals)}")
    lines.append(f"- System signals: {'、'.join(system_signals)}")

    return "\n".join(lines)


def week_label_from_date(date_label: str) -> str:
    week_key = datetime.fromisoformat(date_label).isocalendar()
    return f"{week_key.year}-W{week_key.week:02d}"
