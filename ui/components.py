# ui/components.py
import chainlit as cl

def get_main_actions() -> list[cl.Action]:
    """Кнопки главного меню"""
    return [
        cl.Action(
            name="main_cmd",
            payload={"intent": "show_plan", "action": "show_plan"},  # ✅ Важно: оба поля
            label="📋 Мой план"
        ),
        cl.Action(
            name="main_cmd",
            payload={"intent": "help", "action": "help"},
            label="💡 Подсказка"
        ),
    ]

def get_task_actions(task_id: str) -> list[cl.Action]:
    """Кнопки для конкретной задачи"""
    return [
        cl.Action(
            name="main_cmd",
            payload={"intent": "complete_task", "action": "complete_task", "task_id": task_id},
            label="✅ Выполнено"
        ),
        cl.Action(
            name="main_cmd",
            payload={"intent": "postpone_task", "action": "postpone_task", "task_id": task_id},
            label="📅 Перенести"
        ),
    ]