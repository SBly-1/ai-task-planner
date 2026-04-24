# Архитектура проекта

## Разделение зон

Настя:
- graph/
- utils/validation.py
- utils/storage.py

Ярослав:
- app.py
- ui/
- llm/
- core/

## Контракт между UI и Graph

UI передаёт в граф state.

Минимальные поля state:

- messages
- user_message
- current_step
- task_data
- tasks
- errors
- is_complete
- bot_response
- action

Graph возвращает обновлённый state.

Главное поле для UI:

- bot_response

UI показывает пользователю значение bot_response.

## Правило

graph/ не импортирует ui/.
ui/ не лезет внутрь узлов graph/.
Связь только через state.