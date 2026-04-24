# ui/handlers.py
import chainlit as cl  # ✅ КРИТИЧНО: этот импорт должен быть первым!
import json
from graph.builder import build_graph
from llm.client import get_llm
from llm.prompts import INTENT_SYSTEM
from ui.components import get_main_actions
from ui.formatters import format_plan
from utils.storage import load_tasks

# Инициализация (выполняется один раз при старте сервера)
graph = build_graph()
llm = get_llm()

def parse_intent(text: str) -> dict:
    """Определяет намерение пользователя (простая эвристика + LLM fallback)"""
    text_lower = text.lower()
    
    # Простые ключевые слова для скорости
    if "план" in text_lower or "show" in text_lower or "список" in text_lower:
        return {"intent": "show_plan", "task_data": {}}
    elif "выполн" in text_lower or "done" in text_lower or "готов" in text_lower:
        return {"intent": "complete_task", "task_data": {}}
    elif "перенес" in text_lower or "postpone" in text_lower or "отлож" in text_lower:
        return {"intent": "postpone_task", "task_data": {}}
    elif "помо" in text_lower or "help" in text_lower or "подсказ" in text_lower:
        return {"intent": "help", "task_data": {}}
    
    # Для добавления задачи — пытаемся распарсить строку
    parts = [p.strip() for p in text.split(",")]
    if len(parts) >= 2:  # Минимум "название, дата"
        task_data = {
            "title": parts[0],
            "deadline": parts[1] if len(parts) > 1 else "",
            "duration_minutes": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 60,
            "importance": parts[3].lower().strip() if len(parts) > 3 else "medium",
            "category": parts[4].lower().strip() if len(parts) > 4 else "other"
        }
        return {"intent": "add_task", "task_data": task_data}
    
    # Fallback: если не распарсили — считаем, что это help
    return {"intent": "help", "task_data": {}}

@cl.on_chat_start
async def handle_start():
    """Инициализация чата"""
    state = {
        "messages": [],
        "user_message": "",
        "intent": "add_task",      # стартовое намерение
        "current_step": "greet",
        "task_data": {},
        "tasks": load_tasks(),
        "missing_fields": [],
        "errors": [],
        "is_complete": False,
        "bot_response": None,
        "action": None,
    }
    cl.user_session.set("state", state)
    
    # Запускаем граф
    res = graph.invoke(state)
    cl.user_session.set("state", res)
    
    # Показываем ответ
    await cl.Message(
        content=res.get("bot_response", "👋 Привет!"),
        actions=get_main_actions()
    ).send()

@cl.on_message
async def handle_message(msg: cl.Message):
    """Обработка сообщения от пользователя"""
    state = cl.user_session.get("state")
    
    # Определяем намерение
    parsed = parse_intent(msg.content)
    
    # Обновляем состояние
    state["user_message"] = msg.content
    state["intent"] = parsed.get("intent", "unknown")
    state["task_data"] = parsed.get("task_data", {})
    state["action"] = None
    state["messages"].append({"role": "user", "content": msg.content})
    
    # Запускаем граф
    res = graph.invoke(state)
    cl.user_session.set("state", res)
    
    # Показываем ответ
    if state["intent"] == "show_plan":
        await cl.Message(
            content=format_plan(res.get("tasks", [])),
            actions=get_main_actions()
        ).send()
    else:
        await cl.Message(
            content=res.get("bot_response", "🤔"),
            actions=get_main_actions()
        ).send()

@cl.action_callback("main_cmd")
async def handle_action(action: cl.Action):
    """Обработка кнопок"""
    state = cl.user_session.get("state")
    
    # Извлекаем данные из payload кнопки
    intent = action.payload.get("intent", "unknown")
    task_id = action.payload.get("task_id")
    
    # Обновляем состояние
    state["intent"] = intent
    state["action"] = intent  # для handle_action_node
    if task_id:
        state["task_data"]["id"] = task_id
    state["messages"].append({"role": "user", "content": f"[КНОПКА: {intent}]"})
    
    # Запускаем граф
    res = graph.invoke(state)
    cl.user_session.set("state", res)
    
    # Показываем ответ
    if intent == "show_plan":
        await cl.Message(
            content=format_plan(res.get("tasks", [])),
            actions=get_main_actions()
        ).send()
    else:
        await cl.Message(
            content=res.get("bot_response", "✅"),
            actions=get_main_actions()
        ).send()