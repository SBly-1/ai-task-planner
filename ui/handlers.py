import chainlit as cl

from graph.builder import build_graph
from llm.client import parse_user_message
from ui.components import get_main_actions
from ui.formatters import format_plan
from utils.storage import load_tasks


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
    }


async def handle_start():
    state = get_initial_state()

    cl.user_session.set("state", state)

    result = graph.invoke(state)

    cl.user_session.set("state", result)

    await cl.Message(
        content=result.get("bot_response", "Добрый день! Хотите добавить задачу?"),
        actions=get_main_actions(),
    ).send()


async def handle_message(msg: cl.Message):
    state = cl.user_session.get("state") or get_initial_state()

    parsed = parse_user_message(msg.content, state)

    state["user_message"] = msg.content
    state["intent"] = parsed.get("intent", "add_task")
    state["task_data"] = parsed.get("task_data", {})
    state["action"] = None
    state.setdefault("messages", []).append({"role": "user", "content": msg.content})

    result = graph.invoke(state)

    result.setdefault("messages", []).append(
        {
            "role": "assistant",
            "content": result.get("bot_response", ""),
        }
    )

    cl.user_session.set("state", result)

    if result.get("current_step") == "plan_ready":
        content = format_plan(result.get("tasks", []))
    else:
        content = result.get("bot_response", "")

    await cl.Message(
        content=content,
        actions=get_main_actions(),
    ).send()


async def handle_action(action: cl.Action):
    state = cl.user_session.get("state") or get_initial_state()

    intent = action.payload.get("intent", "unknown")
    task_id = action.payload.get("task_id")

    state["intent"] = intent
    state["action"] = intent
    state["user_message"] = ""

    if task_id:
        state["task_data"] = {"id": task_id}
    else:
        state["task_data"] = {}

    state.setdefault("messages", []).append({"role": "user", "content": f"[КНОПКА: {intent}]"})

    result = graph.invoke(state)

    result.setdefault("messages", []).append(
        {
            "role": "assistant",
            "content": result.get("bot_response", ""),
        }
    )

    cl.user_session.set("state", result)

    if result.get("current_step") == "plan_ready":
        content = format_plan(result.get("tasks", []))
    else:
        content = result.get("bot_response", "✅")

    await cl.Message(
        content=content,
        actions=get_main_actions(),
    ).send()
