import uuid
from datetime import datetime

from core.scheduler import build_plan
from graph.state import AgentState, TaskData
from utils.storage import append_task, load_tasks, update_task
from utils.validation import get_missing_fields, validate_task


def greet_node(state: AgentState) -> dict:
    response = (
        "👋 Привет! Я твой AI-планировщик задач.\n\n"
        "Я могу помочь добавить задачи, расставить приоритеты и показать план.\n\n"
        "Формат для быстрого добавления:\n"
        "`Название, YYYY-MM-DD, минуты, важность, категория`\n\n"
        "Пример:\n"
        "`Сдать лабу по вебу, 2026-04-25, 120, high, study`\n\n"
        "Важность: `low`, `medium`, `high`.\n"
        "Категории: `study`, `home`, `health`, `rest`, `other`."
    )

    return {
        "bot_response": response,
        "current_step": "greet",
        "is_complete": True,
    }


def _parse_task_from_message(message: str) -> TaskData:
    parts = [part.strip() for part in message.split(",")]

    task: TaskData = {
        "title": parts[0] if len(parts) > 0 else "",
        "deadline": parts[1] if len(parts) > 1 else "",
        "duration_minutes": 60,
        "importance": "medium",
        "category": "other",
    }

    if len(parts) > 2 and parts[2].isdigit():
        task["duration_minutes"] = int(parts[2])

    if len(parts) > 3 and parts[3]:
        task["importance"] = parts[3].lower()

    if len(parts) > 4 and parts[4]:
        task["category"] = parts[4].lower()

    return task


def collect_task_node(state: AgentState) -> dict:
    task_data = dict(state.get("task_data") or {})
    user_message = state.get("user_message", "")

    if not task_data and user_message:
        task_data = _parse_task_from_message(user_message)

    task_data.setdefault("id", str(uuid.uuid4())[:8])
    task_data.setdefault("status", "active")
    task_data.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
    task_data.setdefault("postponed_count", 0)

    return {
        "task_data": task_data,
        "current_step": "collect_task",
        "is_complete": False,
    }


def validate_task_node(state: AgentState) -> dict:
    task_data = state.get("task_data")

    missing_fields = get_missing_fields(task_data)
    errors = validate_task(task_data)

    if missing_fields or errors:
        return {
            "missing_fields": missing_fields,
            "errors": errors,
            "current_step": "validation_failed",
            "is_complete": False,
        }

    return {
        "missing_fields": [],
        "errors": [],
        "current_step": "validated",
        "is_complete": False,
    }


def save_task_node(state: AgentState) -> dict:
    task_data = state.get("task_data")

    if not task_data:
        return {
            "bot_response": "⚠️ Не получилось сохранить задачу: данные задачи пустые.",
            "current_step": "save_failed",
            "is_complete": True,
        }

    append_task(task_data)

    title = task_data.get("title", "Задача")

    return {
        "tasks": load_tasks(),
        "task_data": {},
        "bot_response": f"✅ Задача «{title}» сохранена!",
        "current_step": "task_saved",
        "is_complete": True,
    }


def build_plan_node(state: AgentState) -> dict:
    tasks = load_tasks()
    plan = build_plan(tasks)

    if not plan:
        return {
            "tasks": [],
            "bot_response": "📋 Пока активных задач нет.",
            "current_step": "plan_empty",
            "is_complete": True,
        }

    return {
        "tasks": plan,
        "bot_response": "📋 План готов.",
        "current_step": "plan_ready",
        "is_complete": True,
    }


def handle_action_node(state: AgentState) -> dict:
    action = state.get("action") or state.get("intent")
    task_data = state.get("task_data") or {}
    task_id = task_data.get("id")

    if not task_id:
        return {
            "bot_response": "⚠️ Не выбрана задача для действия.",
            "current_step": "action_failed",
            "is_complete": True,
        }

    if action == "complete_task":
        updated = update_task(task_id, {"status": "completed"})
        if updated:
            return {
                "tasks": load_tasks(),
                "bot_response": "✅ Задача отмечена как выполненная!",
                "current_step": "task_completed",
                "is_complete": True,
            }

        return {
            "bot_response": "⚠️ Не нашла задачу для выполнения.",
            "current_step": "task_not_found",
            "is_complete": True,
        }

    if action == "postpone_task":
        current_count = task_data.get("postponed_count", 0)
        updated = update_task(
            task_id,
            {
                "status": "postponed",
                "postponed_count": current_count + 1,
            },
        )

        if updated:
            return {
                "tasks": load_tasks(),
                "bot_response": f"📅 Задача перенесена. Количество переносов: {current_count + 1}.",
                "current_step": "task_postponed",
                "is_complete": True,
            }

        return {
            "bot_response": "⚠️ Не нашла задачу для переноса.",
            "current_step": "task_not_found",
            "is_complete": True,
        }

    return {
        "bot_response": "⚠️ Неизвестное действие.",
        "current_step": "unknown_action",
        "is_complete": True,
    }


def fallback_node(state: AgentState) -> dict:
    missing_fields = state.get("missing_fields", [])
    errors = state.get("errors", [])

    field_names = {
        "title": "название задачи",
        "deadline": "дедлайн в формате YYYY-MM-DD",
        "duration_minutes": "длительность в минутах",
        "importance": "важность: low / medium / high",
        "category": "категория: study / home / health / rest / other",
    }

    response_parts = []

    if missing_fields:
        response_parts.append("❓ Не хватает данных:")
        response_parts.extend(
            f"• {field_names.get(field, field)}"
            for field in missing_fields
        )

    if errors:
        response_parts.append("\n⚠️ Ошибки:")
        response_parts.extend(f"• {error}" for error in errors)

    response_parts.append(
        "\nПопробуйте формат:\n"
        "`Сдать лабу по вебу, 2026-04-25, 120, high, study`"
    )

    return {
        "bot_response": "\n".join(response_parts),
        "current_step": "fallback",
        "is_complete": True,
    }


def complete_node(state: AgentState) -> dict:
    return {
        "bot_response": state.get("bot_response") or "✅ Готово!",
        "current_step": "complete",
        "is_complete": True,
    }