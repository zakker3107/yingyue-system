from __future__ import annotations

import argparse
import json
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "data" / "processed" / "reports"

TASK_TERMS: dict[str, tuple[str, ...]] = {
    "analysis": ("analysis", "analyze", "review", "optimiz", "summary", "report"),
    "writing": ("write", "writing", "rewrite", "email", "copy", "draft"),
    "coding": ("python", "api", "code", "bug", "fix", "test"),
    "research": ("research", "source", "news", "investigate", "find", "look up"),
    "image": ("image", "logo", "design", "screenshot", "diagram", "photo"),
}

TOPIC_TERMS: dict[str, tuple[str, ...]] = {
    "creative": ("creative", "design", "logo", "branding", "visual", "layout"),
    "analysis": ("analysis", "summary", "metrics", "trend", "review", "insight"),
    "coding": ("python", "api", "code", "bug", "test", "script"),
    "research": ("research", "source", "news", "reference", "study", "compare"),
    "operations": ("daily", "weekly", "monitor", "report", "pipeline", "automation"),
}

@dataclass
class ConversationRecord:
    title: str
    create_time: datetime
    role_counts: Counter[str]
    user_chars: int
    assistant_chars: int
    user_messages: int
    assistant_messages: int
    tools_used: bool
    attachments: int
    task_hits: Counter[str]
    topic_hits: Counter[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate weekly AI usage review from a chat export zip")
    parser.add_argument("--export", required=True, help="Path to exported zip or extracted folder")
    parser.add_argument("--anchor-date", default="", help="Anchor date in YYYY-MM-DD. Defaults to local today.")
    parser.add_argument("--days", type=int, default=7, help="How many days to include, ending on anchor date.")
    parser.add_argument(
        "--output",
        default="",
        help="Markdown output path. Defaults to data/processed/reports/ai_weekly_review_YYYY-Www.md",
    )
    parser.add_argument("--json-output", default="", help="Optional JSON output path")
    return parser.parse_args()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _clean_text(text: str, fallback: str = "") -> str:
    collapsed = " ".join(text.split())
    cleaned = "".join(ch for ch in collapsed if ch == " " or unicodedata.category(ch)[0] != "C")
    if not cleaned:
        return fallback

    suspicious = sum(1 for ch in cleaned if ch == "?" or unicodedata.category(ch) in {"Co", "Cs"})
    if suspicious and suspicious / max(len(cleaned), 1) >= 0.2:
        return fallback or "unreadable text"
    return cleaned


def _load_conversations(export_path: Path) -> list[dict[str, Any]]:
    if export_path.is_dir():
        files = sorted(export_path.glob("conversations-*.json"))
        conversations: list[dict[str, Any]] = []
        for path in files:
            conversations.extend(json.loads(path.read_text(encoding="utf-8", errors="replace")))
        return conversations

    conversations = []
    with zipfile.ZipFile(export_path) as zf:
        names = sorted(name for name in zf.namelist() if Path(name).name.startswith("conversations-") and name.endswith(".json"))
        for name in names:
            with zf.open(name) as handle:
                conversations.extend(json.load(handle))
    return conversations


def _message_text(message: dict[str, Any]) -> tuple[str, int]:
    content = message.get("content") or {}
    parts = content.get("parts") or []
    text_parts: list[str] = []
    attachment_count = 0

    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict):
            if part.get("content_type") == "image_asset_pointer":
                attachment_count += 1
            for key in ("text", "asset_pointer"):
                value = part.get(key)
                if isinstance(value, str):
                    text_parts.append(value)
    return _clean_text("\n".join(text_parts).strip()), attachment_count


def _analyze_conversation(raw: dict[str, Any]) -> ConversationRecord | None:
    timestamp = raw.get("create_time")
    if not timestamp:
        return None

    created = datetime.fromtimestamp(timestamp, UTC).astimezone()
    role_counts: Counter[str] = Counter()
    user_chars = 0
    assistant_chars = 0
    user_messages = 0
    assistant_messages = 0
    tools_used = False
    attachments = 0
    task_hits: Counter[str] = Counter()
    topic_hits: Counter[str] = Counter()

    title = _clean_text(str(raw.get("title") or ""), fallback="Untitled")
    for topic, terms in TOPIC_TERMS.items():
        if _contains_any(title, terms):
            topic_hits[topic] += 1

    for node in (raw.get("mapping") or {}).values():
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue

        role = ((message.get("author") or {}).get("role")) or "unknown"
        role_counts[role] += 1
        metadata = message.get("metadata") or {}
        if metadata.get("aggregate_result"):
            tools_used = True
        if metadata.get("attachments"):
            attachments += len(metadata.get("attachments") or [])

        text, inline_attachments = _message_text(message)
        attachments += inline_attachments
        if not text:
            continue

        if role == "user":
            user_messages += 1
            user_chars += len(text)
            for task, terms in TASK_TERMS.items():
                if _contains_any(text, terms):
                    task_hits[task] += 1
            for topic, terms in TOPIC_TERMS.items():
                if _contains_any(text, terms):
                    topic_hits[topic] += 1
        elif role == "assistant":
            assistant_messages += 1
            assistant_chars += len(text)

    return ConversationRecord(
        title=title,
        create_time=created,
        role_counts=role_counts,
        user_chars=user_chars,
        assistant_chars=assistant_chars,
        user_messages=user_messages,
        assistant_messages=assistant_messages,
        tools_used=tools_used,
        attachments=attachments,
        task_hits=task_hits,
        topic_hits=topic_hits,
    )


def _safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def _pick_priority_actions(summary: dict[str, Any]) -> list[str]:
    actions: list[str] = []

    if summary["avg_user_chars"] < 40:
        actions.append("Encourage richer prompts with goal, constraints, and output format.")
    if summary["short_conversation_ratio"] >= 0.45:
        actions.append("Reduce one-turn chats by asking for the desired outcome earlier.")
    if summary["recurring_ops_ratio"] >= 0.2 or summary["recurring_coding_ratio"] >= 0.15:
        actions.append("Turn repeated operational or coding requests into reusable workflows.")
    if summary["tool_usage_ratio"] < 0.2:
        actions.append("Use local tools more often when verification or file inspection would help.")
    if summary["attachment_conversations"] >= 2:
        actions.append("Add a clearer attachment handling checklist for image and file-heavy threads.")
    if not actions:
        actions.append("Maintain the current collaboration pattern and review again next week.")

    return actions[:3]

def build_summary(records: list[ConversationRecord], start_date: date, end_date: date) -> dict[str, Any]:
    conv_count = len(records)
    total_user_messages = sum(r.user_messages for r in records)
    total_assistant_messages = sum(r.assistant_messages for r in records)
    total_user_chars = sum(r.user_chars for r in records)
    total_assistant_chars = sum(r.assistant_chars for r in records)

    conversation_sizes = [sum(r.role_counts.values()) for r in records]
    short_conversations = sum(1 for size in conversation_sizes if size <= 5)
    tool_count = sum(1 for r in records if r.tools_used)
    attachment_conversations = sum(1 for r in records if r.attachments > 0)

    task_counter: Counter[str] = Counter()
    topic_counter: Counter[str] = Counter()
    for record in records:
        task_counter.update(record.task_hits)
        topic_counter.update(record.topic_hits)

    avg_user_chars = round(_safe_div(total_user_chars, total_user_messages), 1)
    avg_assistant_chars = round(_safe_div(total_assistant_chars, total_assistant_messages), 1)
    response_expansion_ratio = round(_safe_div(avg_assistant_chars, avg_user_chars), 1) if avg_user_chars else 0.0

    summary = {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": (end_date - start_date).days + 1,
        },
        "conversation_count": conv_count,
        "user_messages": total_user_messages,
        "assistant_messages": total_assistant_messages,
        "avg_user_chars": avg_user_chars,
        "avg_assistant_chars": avg_assistant_chars,
        "response_expansion_ratio": response_expansion_ratio,
        "short_conversation_ratio": round(_safe_div(short_conversations, conv_count), 2),
        "tool_usage_ratio": round(_safe_div(tool_count, conv_count), 2),
        "attachment_conversations": attachment_conversations,
        "top_tasks": task_counter.most_common(5),
        "top_topics": topic_counter.most_common(5),
        "recurring_ops_ratio": round(_safe_div(topic_counter.get("operations", 0), max(1, conv_count)), 2),
        "recurring_coding_ratio": round(_safe_div(topic_counter.get("coding", 0), max(1, conv_count)), 2),
        "titles": [r.title for r in sorted(records, key=lambda item: item.create_time, reverse=True)[:10]],
    }
    summary["priority_actions"] = _pick_priority_actions(summary)
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    top_tasks = ", ".join(f"{name}({count})" for name, count in summary["top_tasks"]) or "none"
    top_topics = ", ".join(f"{name}({count})" for name, count in summary["top_topics"]) or "none"

    findings: list[str] = []
    if summary["avg_user_chars"] < 40:
        findings.append("User prompts are short on average, so intent may be underspecified.")
    if summary["short_conversation_ratio"] >= 0.45:
        findings.append("A high share of conversations end quickly, suggesting limited follow-through.")
    if summary["tool_usage_ratio"] < 0.2:
        findings.append("Tool usage is relatively low compared with the amount of operational work.")
    if summary["attachment_conversations"] >= 2:
        findings.append("File or image attachments appear often enough to justify a clearer handling pattern.")
    if not findings:
        findings.append("Usage patterns look stable for this period.")

    lines = [
        "# AI Weekly Review",
        "",
        f"- Period: {summary['period']['start']} to {summary['period']['end']}",
        f"- Conversations: {summary['conversation_count']}",
        f"- User messages: {summary['user_messages']}",
        f"- Assistant messages: {summary['assistant_messages']}",
        f"- Avg user chars: {summary['avg_user_chars']}",
        f"- Avg assistant chars: {summary['avg_assistant_chars']}",
        f"- Response expansion ratio: {summary['response_expansion_ratio']}x",
        f"- Short conversation ratio: {summary['short_conversation_ratio']}",
        f"- Tool usage ratio: {summary['tool_usage_ratio']}",
        "",
        "## Signals",
        f"- Top tasks: {top_tasks}",
        f"- Top topics: {top_topics}",
        f"- Recent titles: {' | '.join(summary['titles']) if summary['titles'] else 'none'}",
        "",
        "## Findings",
    ]
    lines.extend(f"- {item}" for item in findings)
    lines.extend(["", "## Priority Actions"])
    lines.extend(f"- {item}" for item in summary["priority_actions"])
    lines.extend(
        [
            "",
            "## Weekly Checklist",
            "- Review the top repeated task patterns and decide what to standardize.",
            "- Capture 1-3 concrete prompt examples worth reusing next week.",
            "- Check whether more tool-assisted verification would improve accuracy.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    export_path = Path(args.export).expanduser().resolve()
    anchor = date.fromisoformat(args.anchor_date) if args.anchor_date else datetime.now().astimezone().date()
    start = anchor - timedelta(days=max(args.days - 1, 0))

    all_conversations = _load_conversations(export_path)
    records = [record for item in all_conversations if (record := _analyze_conversation(item))]
    period_records = [record for record in records if start <= record.create_time.date() <= anchor]

    if not period_records:
        raise SystemExit(f"No conversations found between {start.isoformat()} and {anchor.isoformat()}")

    summary = build_summary(period_records, start, anchor)

    iso_year, iso_week, _ = anchor.isocalendar()
    output_path = Path(args.output) if args.output else REPORT_DIR / f"ai_weekly_review_{iso_year}-W{iso_week:02d}.md"
    json_output_path = Path(args.json_output) if args.json_output else output_path.with_suffix(".json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(render_markdown(summary), encoding="utf-8")
    json_output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"weekly ai review written: {output_path}")
    print(f"json summary written: {json_output_path}")
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write(payload.encode(sys.stdout.encoding or "utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

