from __future__ import annotations

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
}

ECONOMY_KEYWORDS = (
    "oil",
    "inflation",
    "price",
    "prices",
    "market",
    "economy",
    "tariff",
    "trade",
    "ship",
    "supply",
    "cocoa",
)
TECH_KEYWORDS = (
    "ai",
    "model",
    "chip",
    "semiconductor",
    "platform",
    "software",
    "data",
    "digital",
    "verify",
    "online",
)
POLITICAL_KEYWORDS = (
    "war",
    "attack",
    "leader",
    "election",
    "embassy",
    "police",
    "government",
    "policy",
    "amnesty",
    "terror",
)
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


def _topic_name(bucket: str) -> str:
    return TOPIC_LABELS.get(bucket, bucket)


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _format_percent(value: object) -> str:
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "0.00%"


def _classify_item(item: dict[str, str]) -> str:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    scores = {
        "economy": sum(1 for token in ECONOMY_KEYWORDS if token in text),
        "technology": sum(1 for token in TECH_KEYWORDS if token in text),
        "politics": sum(1 for token in POLITICAL_KEYWORDS if token in text),
    }
    category, score = max(scores.items(), key=lambda pair: pair[1])
    if score == 0:
        topic = str(item.get("topic") or "")
        if topic in {"ai", "technology"}:
            return "technology"
        if topic in {"economy"}:
            return "economy"
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
        f"{observation['observed_date']}：主趨勢 {observation['top_topic']}，"
        f"次軸 {observation['second_topic']}，情緒 {observation['sentiment_label']}。"
    )


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
        categories[_classify_item(item)].append(item)

    city_signals = _pick_signals(news, CITY_KEYWORDS, "城市層訊號仍分散，先追蹤價格、物流與數位服務摩擦。")
    system_signals = _pick_signals(news, SYSTEM_KEYWORDS, "系統層訊號仍分散，先追蹤制度邊界與供應鏈傳導。")

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
    ]

    focus_items = news[:5]
    lines: list[str] = []
    lines.append(f"# 影月系統策略週報 ({week_label})")
    lines.append("")
    lines.append(f"- 生成時間: {generated_at}")
    lines.append(f"- 覆蓋觀察天數: {len(observations)}")
    lines.append(f"- 納入新聞樣本: {len(news)}")
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
        lines.append(f"   - 類別: {category} | 來源: {item['source']} | 主題: {item['topic']}")
        lines.append(f"   - 事件摘要: {item['summary']}")
        lines.append(
            f"   - 日常影響: 建議觀察此事件是否回傳到價格、就業、數位服務或公共安全感受。"
        )
        lines.append(
            f"   - 城市/系統: 檢查它是否改變城市成本結構，或推動監管、供應鏈與制度邊界調整。"
        )
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
    lines.append(f"- Dominant topic: {dominant_topic}")
    lines.append(f"- Top trend: {top_trend.get('bucket', 'general')} / {_format_percent(top_trend.get('metric_value'))}")
    lines.append(f"- Second trend: {second_trend.get('bucket', 'general')} / {_format_percent(second_trend.get('metric_value'))}")
    lines.append(f"- Avg sentiment: {avg_sentiment}")
    lines.append(f"- City signals: {'、'.join(city_signals)}")
    lines.append(f"- System signals: {'、'.join(system_signals)}")

    return "\n".join(lines)


def week_label_from_date(date_label: str) -> str:
    week_key = datetime.fromisoformat(date_label).isocalendar()
    return f"{week_key.year}-W{week_key.week:02d}"
