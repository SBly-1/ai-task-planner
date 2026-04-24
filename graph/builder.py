# graph/builder.py — МИНИМАЛЬНЫЙ ЛИНЕЙНЫЙ ГРАФ (без циклов!)
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import (
    greet_node, collect_task_node, validate_task_node,
    save_task_node, build_plan_node, handle_action_node,
    fallback_node, complete_node
)

def build_graph():
    workflow = StateGraph(AgentState)

    # === Узлы ===
    workflow.add_node("greet", greet_node)
    workflow.add_node("collect_task", collect_task_node)
    workflow.add_node("validate_task", validate_task_node)
    workflow.add_node("save_task", save_task_node)
    workflow.add_node("build_plan", build_plan_node)
    workflow.add_node("handle_action", handle_action_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("complete", complete_node)

    # === Линейные рёбра (НИКАКИХ ЦИКЛОВ) ===
    
    # Старт → приветствие
    workflow.add_edge(START, "greet")
    
    # Приветствие → сбор задачи
    workflow.add_edge("greet", "collect_task")
    
    # Сбор → валидация
    workflow.add_edge("collect_task", "validate_task")
    
    # Валидация: если есть ошибки → fallback (показать ошибку и завершить), иначе → сохранение
    workflow.add_conditional_edges(
        "validate_task",
        lambda s: "fallback" if s.get("missing_fields") else "save_task",
        {"fallback": "fallback", "save_task": "save_task"}
    )
    
    # После сохранения → завершение
    workflow.add_edge("save_task", "complete")
    
    # Поток показа плана
    workflow.add_edge("build_plan", "complete")
    
    # Поток действий (кнопки)
    workflow.add_edge("handle_action", "complete")
    
    # Fallback (ошибки / непонятный ввод) → завершение
    workflow.add_edge("fallback", "complete")
    
    # Завершение → END (критично!)
    workflow.add_edge("complete", END)

    return workflow.compile()