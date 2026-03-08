from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.orchestrator.pipeline import run_agent_pipeline


if __name__ == "__main__":
    result = run_agent_pipeline(context={"limit": 10, "notes": []})
    print(result)
