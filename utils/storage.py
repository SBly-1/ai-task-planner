import json
from pathlib import Path
from typing import List, Dict

# Надёжный путь к data/ вне зависимости от ОС
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TASKS_FILE = DATA_DIR / "tasks.json"

def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_tasks() -> List[Dict]:
    _ensure_dir()
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")
        return []
    try:
        content = TASKS_FILE.read_text(encoding="utf-8")
        return json.loads(content) if content.strip() else []
    except (json.JSONDecodeError, IOError):
        return []

def save_tasks(tasks: List[Dict]) -> None:
    _ensure_dir()
    TASKS_FILE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")

def update_task(task_id: str, updates: Dict) -> bool:
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            task.update(updates)
            save_tasks(tasks)
            return True
    return False