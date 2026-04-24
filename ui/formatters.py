CAT_MAP = {"study":"учёба","home":"быт","health":"здоровье","rest":"отдых","other":"другое"}
IMP_MAP = {"high":"🔥 высокая","medium":"⚡ средняя","low":"🐢 низкая"}

def format_plan(tasks: list[dict]) -> str:
    if not tasks: return "📭 План пуст."
    lines = ["📋 **План на сегодня:**\n"]
    for t in tasks:
        lines.append(f"🔹 **{t.get('title', 'Без названия')}** | {IMP_MAP.get(t.get('importance','low'),'')} | {CAT_MAP.get(t.get('category','other'),'')} | 📅 {t.get('deadline', 'Не указан')} | ⏱ {t.get('duration_minutes', 0)} мин")
    return "\n".join(lines)