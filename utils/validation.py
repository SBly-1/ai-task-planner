from datetime import datetime
from typing import Optional

from graph.state import TaskData


VALID_IMPORTANCE = {"low", "medium", "high"}
VALID_CATEGORIES = {"study", "home", "health", "rest", "other"}


def validate_deadline(deadline: Optional[str]) -> list[str]:
    errors = []

    if not deadline:
        errors.append("Не указан дедлайн.")
        return errors

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except ValueError:
        errors.append("Дедлайн должен быть в формате YYYY-MM-DD.")

    return errors


def validate_duration(duration_minutes: Optional[int]) -> list[str]:
    errors = []

    if duration_minutes is None:
        errors.append("Не указана длительность задачи.")
        return errors

    if not isinstance(duration_minutes, int):
        errors.append("Длительность должна быть числом минут.")
        return errors

    if duration_minutes <= 0:
        errors.append("Длительность должна быть больше 0.")

    return errors


def validate_importance(importance: Optional[str]) -> list[str]:
    errors = []

    if not importance:
        errors.append("Не указана важность задачи.")
        return errors

    if importance not in VALID_IMPORTANCE:
        errors.append("Важность должна быть: low, medium или high.")

    return errors


def validate_category(category: Optional[str]) -> list[str]:
    errors = []

    if not category:
        errors.append("Не указана категория задачи.")
        return errors

    if category not in VALID_CATEGORIES:
        errors.append("Категория должна быть: study, home, health, rest или other.")

    return errors


def get_missing_fields(task: Optional[TaskData]) -> list[str]:
    if task is None:
        return [
            "title",
            "deadline",
            "duration_minutes",
            "importance",
            "category",
        ]

    required_fields = [
        "title",
        "deadline",
        "duration_minutes",
        "importance",
        "category",
    ]

    return [
        field
        for field in required_fields
        if task.get(field) in (None, "")
    ]


def validate_task(task: Optional[TaskData]) -> list[str]:
    errors = []

    if task is None:
        return ["Задача не заполнена."]

    if not task.get("title"):
        errors.append("Не указано название задачи.")

    errors.extend(validate_deadline(task.get("deadline")))
    errors.extend(validate_duration(task.get("duration_minutes")))
    errors.extend(validate_importance(task.get("importance")))
    errors.extend(validate_category(task.get("category")))

    return errors