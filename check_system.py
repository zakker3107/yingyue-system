#!/usr/bin/env python
"""Portable system check with ASCII-only terminal output."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _safe_print(text: str) -> None:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    sys.stdout.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace") + "\n")


_safe_print("=" * 70)
_safe_print("YingYue system file/environment check")
_safe_print("=" * 70)

all_ok = True

_safe_print("\n[Python]")
_safe_print(f"  version: {sys.version.split()[0]}")
_safe_print(f"  executable: {sys.executable}")

_safe_print("\n[Required Files]")
required = {
    "config/sources.json": "news source config",
    "config/philosophy_seed.json": "philosophy seed",
    "data/curated/yingyue.db": "database",
    "scripts/run_mvp.py": "MVP pipeline",
    "scripts/start_api.py": "API starter",
    "scripts/extract_network_events.py": "event extractor",
    "services/api/main.py": "API module",
    ".venv": "virtual environment",
}

for rel_path, desc in required.items():
    exists = (PROJECT_ROOT / rel_path).exists()
    status = "[OK]" if exists else "[FAIL]"
    _safe_print(f"  {status:<6} {rel_path:<40} {desc}")
    if not exists:
        all_ok = False

_safe_print("\n[Dependencies]")
imports = {
    "fastapi": "FastAPI",
    "pydantic": "data validation",
    "feedparser": "RSS parser",
    "sqlite3": "database",
}
for module, desc in imports.items():
    try:
        __import__(module)
        _safe_print(f"  [OK]   {module:<20} {desc}")
    except ImportError:
        _safe_print(f"  [FAIL] {module:<20} {desc} (missing)")
        all_ok = False

_safe_print("\n[Database]")
db_path = PROJECT_ROOT / "data/curated/yingyue.db"
if not db_path.exists():
    _safe_print(f"  [FAIL] missing database: {db_path}")
    all_ok = False
else:
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        _safe_print(f"  [OK]   table_count={len(tables)}")
        for table in tables:
            try:
                count = cursor.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
                _safe_print(f"    - {table}: {count}")
            except Exception as exc:  # noqa: BLE001
                _safe_print(f"    - {table}: ERROR ({exc})")
                all_ok = False
        conn.close()
    except Exception as exc:  # noqa: BLE001
        _safe_print(f"  [FAIL] database check error: {exc}")
        all_ok = False

_safe_print("\n[Config]")
sources_path = PROJECT_ROOT / "config/sources.json"
try:
    with sources_path.open("r", encoding="utf-8-sig") as fh:
        config = json.load(fh)
    sources = config.get("news_sources", [])
    _safe_print(f"  [OK]   sources={len(sources)}")
except Exception as exc:  # noqa: BLE001
    _safe_print(f"  [FAIL] config read error: {exc}")
    all_ok = False

_safe_print("\n[API Module]")
try:
    from services.api import main as api

    checks = ["health", "latest_news", "search_philosophy", "trends_summary", "network_events", "network_event_summary"]
    for name in checks:
        if hasattr(api, name):
            _safe_print(f"  [OK]   {name}")
        else:
            _safe_print(f"  [FAIL] {name} (missing)")
            all_ok = False
except Exception as exc:  # noqa: BLE001
    _safe_print(f"  [FAIL] API module import error: {exc}")
    all_ok = False

_safe_print("\n" + "=" * 70)
_safe_print("RESULT: PASS" if all_ok else "RESULT: FAIL")
_safe_print("=" * 70)
