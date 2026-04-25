from datetime import datetime, timedelta

import chainlit as cl


def _action(label: str, intent: str, action: str, **payload) -> cl.Action:
    return cl.Action(
        name="main_cmd",
        payload={"intent": intent, "action": action, **payload},
        label=label,
    )


def get_main_actions() -> list[cl.Action]:
    """Кнопки главного меню."""
    return [
        _action("📋 Мой план", "show_plan", "show_plan"),
        _action("💡 Подсказка", "help", "help"),
        _action("⚙️ Действия", "actions_menu", "actions_menu"),
        _action("➕ Новая задача", "new_task", "new_task"),
        _action("🗄 Архив", "archive", "archive"),
    ]


def get_cancel_actions() -> list[cl.Action]:
    return [_action("Отмена", "cancel", "cancel")]


def get_new_task_actions() -> list[cl.Action]:
    return [
        _action("Учёба", "add_task", "hint_category", category="study"),
        _action("Обычно", "add_task", "hint_importance", importance="normal"),
        _action("Срочно", "add_task", "hint_importance", importance="high"),
        _action("Сегодня", "add_task", "hint_deadline", deadline=datetime.now().date().isoformat()),
        _action("Завтра", "add_task", "hint_deadline", deadline=(datetime.now().date() + timedelta(days=1)).isoformat()),
        *get_cancel_actions(),
    ]


def get_actions_menu() -> list[cl.Action]:
    return [
        _action("Выполнить задачи", "complete_menu", "complete_menu"),
        _action("Удалить задачи", "delete_menu", "delete_menu"),
        _action("Перенести задачу", "postpone_menu", "postpone_menu"),
        *get_cancel_actions(),
    ]


def get_task_actions(task_id: str) -> list[cl.Action]:
    return [
        _action("Выполнено", "complete_task", "complete_task", task_id=task_id),
        _action("Перенести", "postpone_prepare", "postpone_prepare", task_id=task_id),
        _action("Удалить", "delete_task", "delete_task", task_id=task_id),
        *get_cancel_actions(),
    ]


def get_task_list_actions(tasks: list[dict], action: str) -> list[cl.Action]:
    labels = {
        "complete_task": "Выполнить",
        "delete_task": "Удалить",
        "postpone_prepare": "Перенести",
        "restore_task": "Не выполнена",
    }
    actions = [
        _action(
            f"{labels.get(action, 'Выбрать')}: {task.get('title', 'Задача')[:28]}",
            action,
            action,
            task_id=task.get("id"),
        )
        for task in tasks
        if task.get("id")
    ]
    return actions + get_cancel_actions()


def get_postpone_date_actions(task_id: str) -> list[cl.Action]:
    today = datetime.now().date()
    options = [
        ("Завтра", today + timedelta(days=1)),
        ("Через 2 дня", today + timedelta(days=2)),
        ("Через неделю", today + timedelta(days=7)),
    ]
    return [
        _action(label, "postpone_task", "postpone_task", task_id=task_id, deadline=date.isoformat())
        for label, date in options
    ] + get_cancel_actions()


def get_archive_actions(tasks: list[dict]) -> list[cl.Action]:
    actions: list[cl.Action] = []
    for task in tasks:
        task_id = task.get("id")
        title = task.get("title", "Задача")[:24]
        if not task_id:
            continue
        actions.append(_action(f"Не выполнена: {title}", "restore_task", "restore_task", task_id=task_id))
        actions.append(_action(f"Удалить: {title}", "delete_task", "delete_task", task_id=task_id))
    return actions + get_cancel_actions()
