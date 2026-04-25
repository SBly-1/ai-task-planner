import chainlit as cl

from graph.builder import build_graph
from llm.client import parse_user_message
from ui.components import (
    get_actions_menu,
    get_archive_actions,
    get_cancel_actions,
    get_main_actions,
    get_new_task_actions,
    get_postpone_date_actions,
    get_task_actions,
    get_task_list_actions,
)
from ui.formatters import format_archive, format_plan_by_day, format_tasks_for_action
from utils.storage import delete_task, load_tasks, update_task
from utils.validation import validate_deadline


graph = build_graph()


def get_initial_state() -> dict:
    return {
        "messages": [],
        "user_message": "",
        "intent": "help",
        "current_step": "greet",
        "task_data": {},
        "draft_task": {},
        "tasks": load_tasks(),
        "missing_fields": [],
        "errors": [],
        "is_complete": False,
        "bot_response": None,
        "action": None,
        "mode": None,
        "selected_task_id": None,
    }


def _first_active_task(tasks: list[dict]) -> dict | None:
    return next((task for task in tasks if task.get("status") == "active"), None)


def _active_tasks() -> list[dict]:
    return [task for task in load_tasks() if task.get("status") == "active"]


def _archived_tasks() -> list[dict]:
    return [task for task in load_tasks() if task.get("status") in {"completed", "postponed"}]


def _reminder_text() -> str:
    tired_tasks = [
        task
        for task in load_tasks()
        if task.get("postponed_count", 0) >= 5 and task.get("status") != "completed"
    ]
    if not tired_tasks:
        return ""

    lines = ["\n\nНапоминание: эти задачи уже откладывались много раз, лучше закрыть их поскорее:"]
    for task in tired_tasks[:3]:
        lines.append(f"- {task.get('title', 'Задача')} — переносов: {task.get('postponed_count', 0)}")
    return "\n".join(lines)


def _creation_actions(result: dict) -> list[cl.Action]:
    if result.get("current_step") == "ask_missing_info":
        missing_fields = result.get("missing_fields", [])
        if missing_fields and missing_fields[0] == "title":
            return []
        return get_new_task_actions(missing_fields[:1])
    return get_main_actions()


def _finish_creation_if_saved(result: dict) -> dict:
    if result.get("current_step") == "task_saved":
        result["mode"] = None
        result["selected_task_id"] = None
    return result


def _run_graph_with_state(state: dict, parsed: dict, user_message: str) -> dict:
    state["user_message"] = user_message
    state["intent"] = parsed.get("intent", "add_task")
    state["task_data"] = parsed.get("task_data", {})
    state["action"] = None
    state.setdefault("messages", []).append({"role": "user", "content": user_message})

    result = graph.invoke(state)
    result.setdefault("messages", []).append(
        {"role": "assistant", "content": result.get("bot_response", "")}
    )
    return _finish_creation_if_saved(result)


async def _send_plan() -> None:
    tasks = _active_tasks()
    first_active = _first_active_task(tasks)
    await cl.Message(
        content=format_plan_by_day(tasks),
        actions=get_task_actions(first_active["id"]) if first_active else get_main_actions(),
    ).send()


async def _send_delete_picker() -> None:
    tasks = load_tasks()
    await cl.Message(
        content=format_tasks_for_action(tasks, "Выберите задачу для удаления"),
        actions=get_task_list_actions(tasks, "delete_task") if tasks else get_main_actions(),
    ).send()


async def handle_start():
    state = get_initial_state()
    cl.user_session.set("state", state)

    result = graph.invoke(state)
    result["bot_response"] = (result.get("bot_response") or "") + _reminder_text()
    cl.user_session.set("state", result)

    await cl.Message(
        content=result.get("bot_response", "Добрый день! Хотите добавить задачу?"),
        actions=get_main_actions(),
    ).send()


async def handle_message(msg: cl.Message):
    state = cl.user_session.get("state") or get_initial_state()

    if state.get("mode") == "awaiting_postpone_deadline":
        parsed = parse_user_message(msg.content, state)
        deadline = parsed.get("task_data", {}).get("deadline")
        errors = validate_deadline(deadline)
        task_id = state.get("selected_task_id")

        if not deadline or errors:
            await cl.Message(
                content="Не понял дату переноса. Напишите, например: `завтра`, `25.04` или выберите кнопку.",
                actions=get_postpone_date_actions(task_id) if task_id else get_cancel_actions(),
            ).send()
            return

        task = next((item for item in load_tasks() if item.get("id") == task_id), {})
        count = task.get("postponed_count", 0) + 1
        update_task(task_id, {"deadline": deadline, "status": "active", "postponed_count": count})
        state["mode"] = None
        state["selected_task_id"] = None
        cl.user_session.set("state", state)

        warning = "\n\nЭта задача уже часто переносилась. Стоит запланировать её первой." if count >= 5 else ""
        await cl.Message(
            content=f"Перенёс задачу на {deadline}. Количество переносов: {count}.{warning}",
            actions=get_main_actions(),
        ).send()
        return

    parsed = parse_user_message(msg.content, state)
    result = _run_graph_with_state(state, parsed, msg.content)
    cl.user_session.set("state", result)

    if result.get("current_step") == "plan_ready":
        await _send_plan()
        return

    await cl.Message(
        content=result.get("bot_response", ""),
        actions=_creation_actions(result),
    ).send()


async def handle_action(action: cl.Action):
    state = cl.user_session.get("state") or get_initial_state()
    payload = action.payload or {}
    intent = payload.get("intent", "unknown")
    action_type = payload.get("action")
    task_id = payload.get("task_id")

    state.setdefault("messages", []).append({"role": "user", "content": f"[КНОПКА: {intent}]"})

    if action_type == "cancel":
        state["mode"] = None
        state["selected_task_id"] = None
        state["draft_task"] = {}
        state["task_data"] = {}
        cl.user_session.set("state", state)
        await cl.Message(content="Ок, отменил текущее действие.", actions=get_main_actions()).send()
        return

    if action_type == "help":
        state["intent"] = "help"
        state["action"] = "help"
        result = graph.invoke(state)
        cl.user_session.set("state", result)
        await cl.Message(content=result.get("bot_response", ""), actions=get_main_actions()).send()
        return

    if action_type == "new_task":
        state["mode"] = "new_task"
        state["draft_task"] = {}
        state["task_data"] = {}
        cl.user_session.set("state", state)
        await cl.Message(
            content="Что нужно сделать? Напишите название задачи обычным текстом.",
            actions=[],
        ).send()
        return

    if action_type in {"hint_category", "hint_importance", "hint_deadline", "hint_duration"}:
        task_data = {
            key: payload[key]
            for key in ("category", "importance", "deadline", "duration_minutes")
            if key in payload
        }
        parsed = {"intent": "add_task", "task_data": task_data}
        result = _run_graph_with_state(state, parsed, f"[подсказка: {action_type}]")
        cl.user_session.set("state", result)
        await cl.Message(
            content=result.get("bot_response", ""),
            actions=_creation_actions(result),
        ).send()
        return

    if action_type == "show_plan":
        await _send_plan()
        return

    if action_type == "actions_menu":
        await cl.Message(content="Что сделать с задачами?", actions=get_actions_menu()).send()
        return

    if action_type == "complete_menu":
        tasks = _active_tasks()
        await cl.Message(
            content=format_tasks_for_action(tasks, "Выберите задачу для выполнения"),
            actions=get_task_list_actions(tasks, "complete_task") if tasks else get_main_actions(),
        ).send()
        return

    if action_type == "delete_menu":
        await _send_delete_picker()
        return

    if action_type == "postpone_menu":
        tasks = _active_tasks()
        await cl.Message(
            content=format_tasks_for_action(tasks, "Выберите задачу для переноса"),
            actions=get_task_list_actions(tasks, "postpone_prepare") if tasks else get_main_actions(),
        ).send()
        return

    if action_type == "archive":
        tasks = _archived_tasks()
        await cl.Message(
            content=format_archive(load_tasks()),
            actions=get_archive_actions(tasks) if tasks else get_main_actions(),
        ).send()
        return

    if action_type == "complete_task" and task_id:
        update_task(task_id, {"status": "completed"})
        await cl.Message(content="Задача отмечена выполненной.", actions=get_main_actions()).send()
        return

    if action_type == "restore_task" and task_id:
        update_task(task_id, {"status": "active"})
        await cl.Message(content="Вернул задачу в активный план.", actions=get_main_actions()).send()
        return

    if action_type == "delete_task" and task_id:
        deleted = delete_task(task_id)
        text = "Задача удалена." if deleted else "Не нашёл задачу для удаления."
        await cl.Message(content=text, actions=get_main_actions()).send()
        return

    if action_type == "postpone_prepare" and task_id:
        state["mode"] = "awaiting_postpone_deadline"
        state["selected_task_id"] = task_id
        cl.user_session.set("state", state)
        await cl.Message(
            content="На какую дату перенести задачу? Можно выбрать вариант или написать дату текстом.",
            actions=get_postpone_date_actions(task_id),
        ).send()
        return

    if action_type == "postpone_task" and task_id:
        task = next((item for item in load_tasks() if item.get("id") == task_id), {})
        count = task.get("postponed_count", 0) + 1
        deadline = payload.get("deadline")
        updates = {"status": "active", "postponed_count": count}
        if deadline:
            updates["deadline"] = deadline
        update_task(task_id, updates)
        state["mode"] = None
        state["selected_task_id"] = None
        cl.user_session.set("state", state)
        warning = "\n\nЭта задача уже часто переносилась. Стоит выполнить её поскорее." if count >= 5 else ""
        await cl.Message(
            content=f"Задача перенесена. Количество переносов: {count}.{warning}",
            actions=get_main_actions(),
        ).send()
        return

    await cl.Message(content="Не понял действие. Вернул главное меню.", actions=get_main_actions()).send()
