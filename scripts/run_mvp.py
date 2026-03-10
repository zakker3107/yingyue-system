from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from pipelines.orchestrator import run_pipeline


if __name__ == "__main__":
    result = run_pipeline()
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    sys.stdout.buffer.write(payload.encode(sys.stdout.encoding or "utf-8", errors="replace"))
    sys.stdout.buffer.write(b"\n")

