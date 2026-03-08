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
_safe_print("YingYue system integrity check")
_safe_print("=" * 70)

_safe_print("\n[Python]")
_safe_print(f"  executable: {sys.executable}")
_safe_print(f"  version: {sys.version.split()[0]}")
_safe_print(f"  cwd: {Path.cwd()}")

_safe_print("\n[Critical Files]")
critical_files = [
    ("config/sources.json", "news source config"),
    ("config/philosophy_seed.json", "philosophy seed"),
    ("data/curated/yingyue.db", "database"),
    (".venv", "virtual environment"),
]

for path_str, desc in critical_files:
    path = PROJECT_ROOT / path_str
    status = "[OK]" if path.exists() else "[FAIL]"
    _safe_print(f"  {status:<6} {path_str:<35} {desc}")

_safe_print("\n[Config]")
try:
    with (PROJECT_ROOT / "config/sources.json").open("r", encoding="utf-8-sig") as fh:
        config = json.load(fh)
    sources = config.get("news_sources", [])
    _safe_print(f"  [OK]   news_sources={len(sources)}")
    for s in sources[:2]:
        _safe_print(f"    - {s.get('name', 'unknown')}")
except Exception as exc:  # noqa: BLE001
    _safe_print(f"  [FAIL] config read error: {exc}")

_safe_print("\n[Database]")
try:
    db_path = PROJECT_ROOT / "data/curated/yingyue.db"
    if not db_path.exists():
        _safe_print("  [FAIL] database missing")
    else:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        _safe_print(f"  [OK]   table_count={len(tables)}")

        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                _safe_print(f"    {table}: {count}")
            except Exception:
                pass

        conn.close()
except Exception as exc:  # noqa: BLE001
    _safe_print(f"  [FAIL] database check error: {exc}")

_safe_print("\n[API Module]")
try:
    from services.api import main as api

    test_funcs = [
        ("health", lambda: len(api.health()) > 0),
        ("latest_news", lambda: isinstance(api.latest_news(limit=1), list)),
        ("network_events", lambda: isinstance(api.network_events(), list)),
    ]

    for name, test in test_funcs:
        try:
            if test():
                _safe_print(f"  [OK]   {name}")
            else:
                _safe_print(f"  [FAIL] {name} returned unexpected type")
        except Exception as exc:  # noqa: BLE001
            _safe_print(f"  [FAIL] {name}: {exc}")
except Exception as exc:  # noqa: BLE001
    _safe_print(f"  [FAIL] API module import error: {exc}")

_safe_print("\n" + "=" * 70)
_safe_print("Check completed")
_safe_print("=" * 70)
