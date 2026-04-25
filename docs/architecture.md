# Архитектура

Проект разделён на слои:

- `app.py` — входная точка Chainlit.
- `ui/` — обработчики сообщений, кнопки и форматирование ответов.
- `graph/` — LangGraph-сценарий диалога.
- `llm/` — промпт и извлечение структуры задачи из текста.
- `core/` — сортировка и планирование задач.
- `utils/` — валидация и JSON-хранилище.
- `data/` — runtime-данные и шаблоны.
- `tests/` — быстрые проверки логики.

## State

Граф принимает и возвращает `AgentState`:

- `messages`
- `user_message`
- `intent`
- `current_step`
- `task_data`
- `draft_task`
- `tasks`
- `missing_fields`
- `errors`
- `is_complete`
- `bot_response`
- `action`

## Диалоговый граф

Сценарий построен через `StateGraph`:

`START -> route_intent -> greet | collect_task | build_plan | handle_action`

Для добавления задачи:

`collect_task -> validate_task -> ask_missing_info | save_task -> complete -> END`

Граф не содержит обратных рёбер, поэтому один вызов не зацикливается. Продолжение
диалога происходит через сохранённый `draft_task` в Chainlit-сессии.

## Контракт UI и Graph

UI передаёт сообщение пользователя в state, запускает граф и показывает
`bot_response` или отформатированный план. Graph не импортирует `ui/`; связь
идёт только через state.
