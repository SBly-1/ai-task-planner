# graph/nodes.py — МИНИМАЛЬНАЯ ВЕРСИЯ (без current_step / next_node)
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from .state import AgentState, TaskData
from utils.storage import load_tasks, save_tasks, update_task
from core.scheduler import build_plan


def greet_node(state: AgentState) -> dict:
    """Приветствие + инструкция"""
    response = (
        "👋 Привет! Я твой ИИ-планировщик.\n\n"
        "📝 **Как добавить задачу:**\n"
        "`Название, ГГГГ-ММ-ДД, минуты, важность, категория`\n"
        "Пример: `Сдать лабу, 2024-05-20, 60, high, study`\n\n"
        "🔘 Или используй кнопки ниже."
    )
    return {"bot_response": response}


def collect_task_node(state: AgentState) -> dict:
    """Извлекает данные задачи из user_message"""
    raw = state.get("user_message", {})
    
    # Если пришла строка — парсим
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
        raw = {
            "title": parts[0] if len(parts) > 0 else "",
            "deadline": parts[1] if len(parts) > 1 else "",
            "duration_minutes": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 60,
            "importance": parts[3].lower().strip() if len(parts) > 3 else "medium",
            "category": parts[4].lower().strip() if len(parts) > 4 else "other"
        }
    
    task = state.get("task_data", {})
    task.update(raw)
    
    # Дефолтные значения
    task.setdefault("id", str(uuid.uuid4())[:8])
    task.setdefault("status", "active")
    task.setdefault("postponed_count", 0)
    task.setdefault("created_at", datetime.now().isoformat())
    
    return {"task_data": task}


def validate_task_node(state: AgentState) -> dict:
    """Проверяет обязательные поля"""
    t = state.get("task_data", {})
    required = ["title", "deadline", "duration_minutes", "importance", "category"]
    missing = [f for f in required if not t.get(f)]
    return {"missing_fields": missing}  # пустой список = валидация прошла


def save_task_node(state: AgentState) -> dict:
    """Сохраняет задачу"""
    task = state.get("task_data", {})
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)
    title = task.get("title", "Задача")
    return {"bot_response": f"✅ Задача '{title}' сохранена!"}


def build_plan_node(state: AgentState) -> dict:
    """Строит план"""
    tasks = load_tasks()
    plan = build_plan(tasks)
    return {"tasks": plan, "bot_response": "📋 План готов (нажми кнопку для просмотра)"}


def handle_action_node(state: AgentState) -> dict:
    """Обрабатывает кнопки"""
    action = state.get("action")
    task_data = state.get("task_data", {})
    task_id = task_data.get("id")
    
    if not task_id:
        return {"bot_response": "⚠️ Не указана задача"}
    
    if action == "complete_task":
        update_task(task_id, {"status": "completed"})
        msg = "✅ Отмечено как выполненное! 🎉"
    elif action == "postpone_task":
        new_count = task_data.get("postponed_count", 0) + 1
        update_task(task_id, {"status": "postponed", "postponed_count": new_count})
        msg = f"📅 Перенесено (попытка #{new_count})"
    else:
        msg = "🤔 Неизвестное действие"
    
    return {"bot_response": msg}


def fallback_node(state: AgentState) -> dict:
    """Обработчик ошибок / непонятного ввода"""
    missing = state.get("missing_fields", [])
    if missing:
        fields_ru = {
            "title": "название", "deadline": "дедлайн (ГГГГ-ММ-ДД)",
            "duration_minutes": "минуты", "importance": "важность (low/medium/high)",
            "category": "категория (study/home/health/rest/other)"
        }
        prompt = "❓ Не хватает:\n" + "\n".join(f"• {fields_ru.get(f, f)}" for f in missing)
        return {"bot_response": prompt}
    
    return {"bot_response": "🤖 Не понял. Попробуй формат: `Название, ГГГГ-ММ-ДД, минуты, важность, категория`"}


def complete_node(state: AgentState) -> dict:
    """Финальный узел — помечает завершение"""
    state["is_complete"] = True
    if not state.get("bot_response"):
        state["bot_response"] = "✅ Готово!"
    return state  # ← без current_step / next_node!