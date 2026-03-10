from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.reporting.strategic_report import generate_strategic_weekly_report
from services.core.storage import initialize_db


if __name__ == "__main__":
    initialize_db()
    result = generate_strategic_weekly_report()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write(payload.encode(sys.stdout.encoding or "utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")

