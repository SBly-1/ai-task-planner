from datetime import datetime
from typing import Optional

from graph.state import TaskData


VALID_IMPORTANCE = {"low", "normal", "medium", "high"}
VALID_CATEGORIES = {"study", "home", "health", "rest", "other"}


def validate_deadline(deadline: Optional[str]) -> list[str]:
    if not deadline:
        return []

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except ValueError:
        return ["Дедлайн должен быть в формате YYYY-MM-DD."]

    return []


def validate_duration(duration_minutes: Optional[int]) -> list[str]:
    if duration_minutes is None:
        return []

    if not isinstance(duration_minutes, int):
        return ["Длительность должна быть числом минут."]

    if duration_minutes <= 0:
        return ["Длительность должна быть больше 0."]

    return []


def validate_importance(importance: Optional[str]) -> list[str]:
    if not importance:
        return []

    if importance not in VALID_IMPORTANCE:
        return ["Важность должна быть: low, normal, medium или high."]

    return []


def validate_category(category: Optional[str]) -> list[str]:
    if not category:
        return []

    if category not in VALID_CATEGORIES:
        return ["Категория должна быть: study, home, health, rest или other."]

    return []


def get_missing_fields(task: Optional[TaskData]) -> list[str]:
    required_fields = [
        "title",
        "duration_minutes",
        "deadline",
        "importance",
        "category",
    ]

    if task is None:
        return required_fields

    return [
        field
        for field in required_fields
        if task.get(field) in (None, "")
    ]


def validate_task(task: Optional[TaskData]) -> list[str]:
    if task is None:
        return []

    errors = []

    errors.extend(validate_deadline(task.get("deadline")))
    errors.extend(validate_duration(task.get("duration_minutes")))
    errors.extend(validate_importance(task.get("importance")))
    errors.extend(validate_category(task.get("category")))

    return errors
