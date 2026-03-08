from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = PROJECT_ROOT / "data" / "processed" / "reports"
MONITOR_DIR = REPORT_DIR / "monitoring"
DEFAULT_ACCOUNT_LOG = PROJECT_ROOT / "data" / "raw" / "account_activity.jsonl"
DEFAULT_NETWORK_LOG = PROJECT_ROOT / "data" / "raw" / "network_activity.jsonl"
DEFAULT_PIPELINE = REPORT_DIR / "agent_pipeline_latest.json"


@dataclass
class Rule:
    rule_id: str
    title: str
    severity: str
    condition: str
    action: str
    rationale: str


def _load_json_or_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return []

    if raw.startswith("["):
        data = json.loads(raw)
        return [item for item in data if isinstance(item, dict)]

    records: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            records.append(item)
    return records


def _safe_lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _extract_ts_hour(record: dict[str, Any]) -> int | None:
    for key in ("timestamp", "time", "created_at", "occurred_at", "published_at"):
        val = record.get(key)
        if not val:
            continue
        text = str(val).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text).hour
        except ValueError:
            continue
    return None


def _is_failed_auth(record: dict[str, Any]) -> bool:
    text = " ".join(
        [
            _safe_lower(record.get("event_type")),
            _safe_lower(record.get("action")),
            _safe_lower(record.get("status")),
            _safe_lower(record.get("result")),
            _safe_lower(record.get("message")),
        ]
    )
    if "login" not in text and "auth" not in text and "sign" not in text:
        return False
    return any(marker in text for marker in ("fail", "denied", "invalid", "blocked", "unauthorized"))


def _is_suspicious_account_event(record: dict[str, Any]) -> bool:
    text = " ".join(
        [
            _safe_lower(record.get("event_type")),
            _safe_lower(record.get("action")),
            _safe_lower(record.get("status")),
            _safe_lower(record.get("message")),
        ]
    )
    if any(marker in text for marker in ("impossible travel", "bot", "credential stuffing", "new device")):
        return True
    risk_score = record.get("risk_score")
    if isinstance(risk_score, (int, float)) and risk_score >= 70:
        return True
    return False


def _extract_domain(record: dict[str, Any]) -> str:
    url = str(record.get("url") or "").strip()
    domain = str(record.get("domain") or "").strip().lower()
    if domain:
        return domain
    if not url:
        return ""
    parsed = urlparse(url)
    return (parsed.netloc or "").lower()


def _is_risky_domain(domain: str) -> bool:
    if not domain:
        return False
    bad_markers = ("temp", "free", "track", "unknown", "proxy", "vpn", "cdn")
    return any(marker in domain for marker in bad_markers)


def _load_monitor_snapshots(monitor_dir: Path) -> list[dict[str, Any]]:
    if not monitor_dir.exists():
        return []
    snapshots: list[dict[str, Any]] = []
    for path in sorted(monitor_dir.glob("d1_monitor_*.jsonl")):
        snapshots.extend(_load_json_or_jsonl(path))
    return snapshots


def _load_pipeline_news_links(path: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return []

    scout = data.get("agent_pipeline", {}).get("scout", {})
    news_items = scout.get("news_items", [])
    links: list[str] = []
    if isinstance(news_items, list):
        for item in news_items:
            if isinstance(item, dict) and item.get("link"):
                links.append(str(item["link"]))
    return links


def _rules_from_stats(
    account_events: list[dict[str, Any]],
    network_events: list[dict[str, Any]],
    monitor_snapshots: list[dict[str, Any]],
    pipeline_links: list[str],
) -> tuple[list[Rule], dict[str, Any]]:
    total_account = len(account_events)
    failed_auth = sum(1 for rec in account_events if _is_failed_auth(rec))
    suspicious_account = sum(1 for rec in account_events if _is_suspicious_account_event(rec))

    off_hour_account = 0
    for rec in account_events:
        hour = _extract_ts_hour(rec)
        if hour is not None and (hour < 6 or hour >= 23):
            off_hour_account += 1

    domains = [_extract_domain(rec) for rec in network_events]
    domains = [d for d in domains if d]
    domain_counter = Counter(domains)
    risky_domains = sum(1 for d in domains if _is_risky_domain(d))

    monitor_fail = 0
    monitor_total = 0
    for snap in monitor_snapshots:
        overall = _safe_lower(snap.get("overall"))
        if overall:
            monitor_total += 1
            if overall == "fail":
                monitor_fail += 1
    fail_ratio = (monitor_fail / monitor_total) if monitor_total else 0.0

    duplicate_ratio = 0.0
    if pipeline_links:
        unique_links = len(set(pipeline_links))
        duplicate_ratio = 1 - (unique_links / len(pipeline_links))

    rules: list[Rule] = []

    if failed_auth >= 3:
        rules.append(
            Rule(
                rule_id="auth-001",
                title="登入失敗升級防護",
                severity="high",
                condition=f"24h 內登入失敗 >= 3 次 (目前: {failed_auth})",
                action="啟用強制二階段驗證，並暫時鎖定高風險來源 30 分鐘。",
                rationale="帳號活動顯示連續失敗登入，需降低撞庫與暴力嘗試風險。",
            )
        )

    if off_hour_account >= 2:
        rules.append(
            Rule(
                rule_id="auth-002",
                title="深夜異常登入警示",
                severity="medium",
                condition=f"23:00-06:00 的帳號事件 >= 2 次 (目前: {off_hour_account})",
                action="深夜登入改為先通知，未回應則要求額外驗證。",
                rationale="非一般時段活動增加，建議加上條件式驗證。",
            )
        )

    if suspicious_account >= 1:
        rules.append(
            Rule(
                rule_id="auth-003",
                title="高風險事件即時阻擋",
                severity="high",
                condition=f"偵測到可疑帳號事件 >= 1 次 (目前: {suspicious_account})",
                action="立即標記會話為高風險，限制敏感操作，並寫入安全稽核。",
                rationale="已有高風險指標，應啟用即時保護策略。",
            )
        )

    if risky_domains >= 5:
        rules.append(
            Rule(
                rule_id="net-001",
                title="可疑網域存取限制",
                severity="high",
                condition=f"可疑網域活動 >= 5 次 (目前: {risky_domains})",
                action="把可疑網域加入阻擋名單，並輸出人工複核清單。",
                rationale="網路活動中可疑網域占比升高，需降低資料外洩風險。",
            )
        )

    if fail_ratio >= 0.2:
        rules.append(
            Rule(
                rule_id="svc-001",
                title="API 不穩定自動復原",
                severity="high",
                condition=f"監控 FAIL 比例 >= 20% (目前: {fail_ratio:.1%})",
                action="自動觸發 quick_recovery，並縮短監控間隔至 10 分鐘。",
                rationale="服務穩定度不足，需提高恢復速度與可觀測性。",
            )
        )

    if duplicate_ratio >= 0.3:
        rules.append(
            Rule(
                rule_id="content-001",
                title="重複內容去重規則",
                severity="medium",
                condition=f"來源連結重複比例 >= 30% (目前: {duplicate_ratio:.1%})",
                action="在 pipeline 寫入 link 去重，重複內容僅保留首筆。",
                rationale="網路資訊重複會降低報告品質與判讀效率。",
            )
        )

    if not rules:
        rules.append(
            Rule(
                rule_id="base-001",
                title="基線監控規則",
                severity="low",
                condition="目前未觀察到明顯異常模式",
                action="維持每日規則重算，若連續 7 天穩定則維持現行策略。",
                rationale="資料樣本偏少或行為穩定，先維持基線以避免過度調整。",
            )
        )

    stats = {
        "account_event_count": total_account,
        "network_event_count": len(network_events),
        "failed_auth_count": failed_auth,
        "off_hour_account_count": off_hour_account,
        "suspicious_account_count": suspicious_account,
        "monitor_snapshots": monitor_total,
        "monitor_fail_count": monitor_fail,
        "monitor_fail_ratio": round(fail_ratio, 4),
        "network_top_domains": domain_counter.most_common(10),
        "risky_domain_count": risky_domains,
        "pipeline_link_count": len(pipeline_links),
        "pipeline_duplicate_ratio": round(duplicate_ratio, 4),
    }
    return rules, stats


def _write_outputs(
    report_date: str,
    rules: list[Rule],
    stats: dict[str, Any],
    source_paths: dict[str, str],
) -> tuple[Path, Path]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / "activity_rules_latest.json"
    md_path = REPORT_DIR / f"activity_rules_{report_date}.md"

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": report_date,
        "source_paths": source_paths,
        "stats": stats,
        "rules": [
            {
                "id": r.rule_id,
                "title": r.title,
                "severity": r.severity,
                "condition": r.condition,
                "action": r.action,
                "rationale": r.rationale,
            }
            for r in rules
        ],
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Activity Rules (Local Only)",
        "",
        f"- Generated At: {payload['generated_at']}",
        f"- Date: {report_date}",
        f"- Account Events: {stats['account_event_count']}",
        f"- Network Events: {stats['network_event_count']}",
        f"- Monitor Fail Ratio: {stats['monitor_fail_ratio']:.2%}",
        "",
        "## Rules",
    ]
    for r in rules:
        lines.append(f"- [{r.severity.upper()}] {r.title} ({r.rule_id})")
        lines.append(f"  - Condition: {r.condition}")
        lines.append(f"  - Action: {r.action}")
        lines.append(f"  - Rationale: {r.rationale}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate account/network activity rules (local only)")
    parser.add_argument("--account-log", default=str(DEFAULT_ACCOUNT_LOG))
    parser.add_argument("--network-log", default=str(DEFAULT_NETWORK_LOG))
    parser.add_argument("--monitor-dir", default=str(MONITOR_DIR))
    parser.add_argument("--pipeline-json", default=str(DEFAULT_PIPELINE))
    parser.add_argument("--date", default=datetime.now().date().isoformat())
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    account_path = Path(args.account_log)
    network_path = Path(args.network_log)
    monitor_dir = Path(args.monitor_dir)
    pipeline_path = Path(args.pipeline_json)

    account_events = _load_json_or_jsonl(account_path)
    network_events = _load_json_or_jsonl(network_path)
    monitor_snapshots = _load_monitor_snapshots(monitor_dir)
    pipeline_links = _load_pipeline_news_links(pipeline_path)

    rules, stats = _rules_from_stats(account_events, network_events, monitor_snapshots, pipeline_links)
    json_path, md_path = _write_outputs(
        report_date=args.date,
        rules=rules,
        stats=stats,
        source_paths={
            "account_log": str(account_path),
            "network_log": str(network_path),
            "monitor_dir": str(monitor_dir),
            "pipeline_json": str(pipeline_path),
        },
    )

    print(f"rules generated: {json_path}")
    print(f"markdown report: {md_path}")
    print(f"rules_count={len(rules)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
