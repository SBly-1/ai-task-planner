import chainlit as cl


def get_main_actions() -> list[cl.Action]:
    return [
        cl.Action(name="main_cmd", payload={"intent": "show_plan"}, label="📋 Мой план"),
        cl.Action(name="main_cmd", payload={"intent": "complete_task"}, label="✅ Выполнено"),
        cl.Action(name="main_cmd", payload={"intent": "postpone_task"}, label="📅 Перенести"),
        cl.Action(name="main_cmd", payload={"intent": "help"}, label="💡 Подсказка"),
    ]


def get_task_actions(task_id: str) -> list[cl.Action]:
    return [
        cl.Action(name="main_cmd", payload={"intent": "complete_task", "task_id": task_id}, label="✅ Выполнено"),
        cl.Action(name="main_cmd", payload={"intent": "postpone_task", "task_id": task_id}, label="📅 Перенести"),
    ]
