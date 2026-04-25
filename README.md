# AI Task Planner

AI-планировщик задач для студентов: бот принимает задачи обычным текстом,
уточняет недостающие поля, валидирует ввод, сохраняет задачи в JSON и показывает
план по приоритетам.

## Стек

- Python 3.11
- Chainlit
- LangGraph
- OpenAI API
- GPT-4o-mini
- JSON-хранение

## Запуск

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
chainlit run app.py
```

В `.env` укажите `OPENAI_API_KEY`. По умолчанию используется
`LLM_PROVIDER=openai` и `OPENAI_MODEL=gpt-4o-mini`.

## Пример

Пользователь: `завтра сделать лабу по вебу на 2 часа, срочно`

Бот извлекает задачу, категорию, дедлайн, длительность и важность, затем
сохраняет задачу или задаёт уточняющий вопрос.
