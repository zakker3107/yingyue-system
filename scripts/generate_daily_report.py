from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.reporting.daily_report import generate_daily_report
from services.core.storage import initialize_db


if __name__ == "__main__":
    initialize_db()
    result = generate_daily_report()
    print(json.dumps(result, ensure_ascii=False, indent=2))
