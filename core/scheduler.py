# core/scheduler.py
from datetime import datetime
from typing import List, Dict

def _priority_score(task: Dict) -> int:
    """Считает вес задачи: важность + срочность"""
    imp_map = {"high": 30, "medium": 20, "low": 10}
    imp_score = imp_map.get(task.get("importance", "low"), 10)
    
    try:
        dl = datetime.strptime(task.get("deadline", "2099-01-01"), "%Y-%m-%d")
        days_left = (dl - datetime.now()).days
        time_score = max(0, 100 - (days_left * 5))  # чем ближе дедлайн, тем выше скор
    except (ValueError, TypeError):
        time_score = 50  # задачи без даты — в середину
        
    return imp_score + time_score

def build_plan(tasks: List[Dict]) -> List[Dict]:
    """Возвращает активные задачи, отсортированные по приоритету"""
    active = [t for t in tasks if t.get("status") == "active"]
    return sorted(active, key=_priority_score, reverse=True)