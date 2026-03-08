from __future__ import annotations


def dispatch(task_name: str, payload: dict[str, object]) -> dict[str, object]:
    return {"task": task_name, "accepted": True, "payload": payload}
