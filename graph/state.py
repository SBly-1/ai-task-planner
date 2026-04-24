from typing import List, Optional, TypedDict

class TaskData(TypedDict, total=False):
    id: str
    title: str
    deadline: str
    duration_minutes: int
    importance: str
    category: str
    status: str
    created_at: str
    postponed_count: int

class AgentState(TypedDict, total=False):
    messages: List[dict]
    user_message: str
    intent: str
    current_step: str
    task_data: Optional[TaskData]  # ✅ Исправлено: добавлено двоеточие и правильное имя
    tasks: List[TaskData]
    missing_fields: List[str]
    errors: List[str]
    is_complete: bool
    bot_response: Optional[str]
    action: Optional[str]