from __future__ import annotations

from datetime import datetime, timedelta


def next_daily_run(hour: int = 8, minute: int = 30) -> str:
    now = datetime.now()
    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if scheduled <= now:
        scheduled = scheduled + timedelta(days=1)
    return scheduled.isoformat()
