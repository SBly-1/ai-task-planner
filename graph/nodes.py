import uuid
from datetime import datetime

from core.scheduler import build_plan
from graph.state import AgentState, TaskData
from utils.storage import append_task, load_tasks, update_task
from utils.validation import get_missing_fields, validate_task


def route_intent_node(state: AgentState) -> dict:
    return {}


def greet_node(state: AgentState) -> dict:
    response = (
        "Добрый день! Я AI-планировщик задач.\n\n"
        "Хотите добавить задачу? Напишите её обычным текстом.\n"
        "Например: `Лаба по вебу`, `завтра купить продукты на 30 минут`, "
        "`подготовиться к алгебре, 2 часа, важно`.\n\n"
        "Если данных не хватит, я сам уточню."
    )

    return {
        "bot_response": response,
        "current_step": "greet",
        "is_complete": True,
    }


def _merge_task_data(old_task: TaskData | None, new_task: TaskData | None) -> TaskData:
    merged: TaskData = {}

    if old_task:
        merged.update(old_task)

    if new_task:
        for key, value in new_task.items():
            if value not in (None, "", [], {}):
                merged[key] = value

    return merged


def _fill_defaults(task: TaskData) -> TaskData:
    if task.get("title"):
        task.setdefault("id", str(uuid.uuid4())[:8])
        task.setdefault("importance", "normal")
        task.setdefault("status", "active")
        task.setdefault("created_at", datetime.now().isoformat(timespec="seconds"))
        task.setdefault("postponed_count", 0)

    return task


def collect_task_node(state: AgentState) -> dict:
    incoming_task = state.get("task_data") or {}
    draft_task = state.get("draft_task") or {}

    task = _merge_task_data(draft_task, incoming_task)
    task = _fill_defaults(task)

    return {
        "task_data": task,
        "draft_task": task,
        "current_step": "collect_task",
        "is_complete": False,
    }


def validate_task_node(state: AgentState) -> dict:
    task_data = state.get("task_data")

    missing_fields = get_missing_fields(task_data)
    errors = validate_task(task_data)

    return {
        "missing_fields": missing_fields,
        "errors": errors,
        "draft_task": task_data,
        "current_step": "validated" if not missing_fields and not errors else "validation_failed",
        "is_complete": False,
    }


def _question_for_missing_field(field: str, task: TaskData | None) -> str:
    task_title = task.get("title") if task else None

    questions = {
        "title": "Что именно нужно сделать?",
        "duration_minutes": (
            f"Отлично, задача «{task_title}» добавлена. Сколько времени она займёт? "
            "Например: `2 часа` или `30 минут`."
            if task_title
            else "Сколько времени займёт задача? Например: `2 часа` или `30 минут`."
        ),
        "deadline": "Когда дедлайн? Можно написать: `сегодня`, `завтра`, `25.04` или `2026-04-25`.",
        "importance": "Насколько это важно? Напишите: `low`, `medium`, `high` или по-русски: `низкая`, `средняя`, `важно`.",
        "category": "К какой категории отнести задачу? Варианты: `study`, `home`, `health`, `rest`, `other`.",
    }

    return questions.get(field, "Уточните недостающие данные.")


def ask_missing_info_node(state: AgentState) -> dict:
    missing_fields = state.get("missing_fields", [])
    errors = state.get("errors", [])
    task = state.get("task_data")

    response_parts = []

    if errors:
        response_parts.append("⚠️ Есть небольшая ошибка:")
        response_parts.extend(f"• {error}" for error in errors)

    if missing_fields:
        next_field = missing_fields[0]
        response_parts.append(_question_for_missing_field(next_field, task))

    if not response_parts:
        response_parts.append("Уточните, пожалуйста, данные задачи.")

    return {
        "bot_response": "\n".join(response_parts),
        "current_step": "ask_missing_info",
        "is_complete": True,
    }


def save_task_node(state: AgentState) -> dict:
    task_data = state.get("task_data")

    if not task_data:
        return {
            "bot_response": "⚠️ Не получилось сохранить задачу: данные пустые.",
            "current_step": "save_failed",
            "is_complete": True,
        }

    append_task(task_data)

    title = task_data.get("title", "Задача")

    return {
        "tasks": load_tasks(),
        "task_data": {},
        "draft_task": {},
        "missing_fields": [],
        "errors": [],
        "bot_response": f"✅ Задача «{title}» сохранена! Хотите добавить ещё одну или показать план?",
        "current_step": "task_saved",
        "is_complete": True,
    }


def build_plan_node(state: AgentState) -> dict:
    """Строит отсортированный план"""
    tasks = load_tasks()
    plan = build_plan(tasks)  # сортировка по приоритету
    return {
        "tasks": plan,
        "bot_response": "📋 Готово, собрал план по приоритетам.",
        "current_step": "plan_ready",
        "is_complete": True,
    }


def handle_action_node(state: AgentState) -> dict:
    action = state.get("action") or state.get("intent")
    task_data = state.get("task_data") or {}
    task_id = task_data.get("id")
    tasks = build_plan(load_tasks())

    if not task_id:
        first_active = next(
            (task for task in tasks if task.get("status", "active") == "active"),
            None,
        )
        if first_active:
            task_id = first_active.get("id")
            task_data = first_active

    if not task_id:
        return {
            "bot_response": "⚠️ Нет активной задачи для этого действия.",
            "current_step": "action_failed",
            "is_complete": True,
        }

    if action == "complete_task":
        updated = update_task(task_id, {"status": "completed"})
        if updated:
            return {
                "tasks": load_tasks(),
                "bot_response": "✅ Самая приоритетная задача отмечена как выполненная!",
                "current_step": "task_completed",
                "is_complete": True,
            }

    if action == "postpone_task":
        current_count = task_data.get("postponed_count", 0)
        updated = update_task(
            task_id,
            {
                "status": "active",
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
        "bot_response": "⚠️ Не удалось выполнить действие.",
        "current_step": "action_failed",
        "is_complete": True,
    }


def complete_node(state: AgentState) -> dict:
    return {
        "bot_response": state.get("bot_response") or "✅ Готово!",
        "current_step": state.get("current_step") or "complete",
        "is_complete": True,
    }
