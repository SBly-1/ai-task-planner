import json
from pathlib import Path
from typing import Any

from graph.state import AgentState, TaskData


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SESSIONS_DIR = DATA_DIR / "sessions"
TASKS_FILE = DATA_DIR / "tasks.json"


def ensure_data_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path: str | Path, default: Any = None) -> Any:
    path = Path(path)

    if not path.exists():
        return default

    try:
        content = path.read_text(encoding="utf-8")
        if not content.strip():
            return default
        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_tasks() -> list[TaskData]:
    ensure_data_dirs()
    return read_json(TASKS_FILE, default=[])


def save_tasks(tasks: list[TaskData]) -> None:
    ensure_data_dirs()
    write_json(TASKS_FILE, tasks)


def append_task(task: TaskData) -> None:
    tasks = load_tasks()
    tasks.append(task)
    save_tasks(tasks)


def update_task(task_id: str, updates: dict) -> bool:
    tasks = load_tasks()

    for task in tasks:
        if task.get("id") == task_id:
            task.update(updates)
            save_tasks(tasks)
            return True

    return False


def load_session(user_id: str) -> AgentState:
    ensure_data_dirs()
    path = SESSIONS_DIR / f"{user_id}.json"
    return read_json(path, default={})


def save_session(user_id: str, state: AgentState) -> None:
    ensure_data_dirs()
    path = SESSIONS_DIR / f"{user_id}.json"
    write_json(path, state)