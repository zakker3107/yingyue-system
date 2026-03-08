from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = PROJECT_ROOT / "data" / "processed" / "reports" / "activity_rules_latest.json"


def load_rules(path: Path | None = None) -> dict[str, Any]:
    target = path or RULES_PATH
    if not target.exists():
        return {"exists": False, "path": str(target), "rules": []}

    try:
        payload = json.loads(target.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"exists": True, "path": str(target), "rules": [], "error": "invalid_json"}

    rules = payload.get("rules", [])
    if not isinstance(rules, list):
        rules = []
    return {"exists": True, "path": str(target), "rules": rules}


def active_rule_ids(payload: dict[str, Any]) -> list[str]:
    result: list[str] = []
    for item in payload.get("rules", []):
        if isinstance(item, dict) and item.get("id"):
            result.append(str(item["id"]))
    return result


def has_rule(payload: dict[str, Any], rule_id: str) -> bool:
    return rule_id in active_rule_ids(payload)
