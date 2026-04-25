from datetime import datetime
from typing import Dict, List


def _priority_score(task: Dict) -> int:
    importance_score = {
        "high": 40,
        "medium": 25,
        "low": 10,
    }.get(task.get("importance", "low"), 10)

    deadline_score = 0

    try:
        deadline = datetime.strptime(task.get("deadline", "2099-01-01"), "%Y-%m-%d")
        days_left = (deadline.date() - datetime.now().date()).days

        if days_left <= 0:
            deadline_score = 60
        elif days_left == 1:
            deadline_score = 50
        elif days_left <= 3:
            deadline_score = 35
        elif days_left <= 7:
            deadline_score = 20
        else:
            deadline_score = 5
    except ValueError:
        deadline_score = 0

    postponed_score = int(task.get("postponed_count", 0)) * 5

    duration = task.get("duration_minutes") or 0
    short_task_bonus = 5 if duration and duration <= 30 else 0

    return importance_score + deadline_score + postponed_score + short_task_bonus


def build_plan(tasks: List[Dict]) -> List[Dict]:
    active_tasks = [
        task for task in tasks
        if task.get("status", "active") == "active"
    ]

    return sorted(active_tasks, key=_priority_score, reverse=True)
