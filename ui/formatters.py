# ui/formatters.py
from datetime import datetime
from collections import defaultdict

# Маппинг для отображения пользователю
CAT_MAP = {"study":"учёба","home":"быт","health":"здоровье","rest":"отдых","other":"другое"}
IMP_MAP = {"high":"🔥 высокая","medium":"⚡ средняя","low":"🐢 низкая"}
STATUS_MAP = {"active":"⏳ активна","completed":"✅ выполнена","postponed":"📅 отложена"}

def format_date_ru(date_str: str) -> str:
    """Конвертирует YYYY-MM-DD в ДД.ММ.ГГГГ + название дня"""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        days_ru = ["пн","вт","ср","чт","пт","сб","вс"]
        day_name = days_ru[dt.weekday()]
        return f"{dt.strftime('%d.%m')} ({day_name})"
    except:
        return date_str or "Без даты"

def group_tasks_by_date(tasks: list[dict]) -> dict[str, list[dict]]:
    """Группирует задачи по дате дедлайна"""
    grouped = defaultdict(list)
    for t in tasks:
        date = t.get("deadline") or "no-date"
        grouped[date].append(t)
    return dict(grouped)

def format_plan_by_day(tasks: list[dict]) -> str:
    """Форматирует план: задачи сгруппированы по дням, отсортированы по приоритету"""
    if not tasks:
        return "📭 Пока нет активных задач. Добавь первую! 👆"
    
    # Фильтруем только активные задачи
    active = [t for t in tasks if t.get("status") == "active"]
    if not active:
        return "✅ Все задачи выполнены! 🎉\n\nНажми 💡, чтобы добавить новую."
    
    # Сортировка внутри дня: высокий приоритет → короткий дедлайн
    priority_order = {"high": 0, "medium": 1, "low": 2}
    active.sort(key=lambda t: (
        priority_order.get(t.get("importance", "medium"), 1),
        t.get("deadline", "9999-99-99")
    ))
    
    # Группируем по дате
    grouped = group_tasks_by_date(active)
    
    # Сортируем даты: сначала ближайшие
    def date_key(d):
        if d == "no-date":
            return "9999-99-99"
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            return "9999-99-99"
    
    sorted_dates = sorted(grouped.keys(), key=date_key)
    
    # Формируем вывод
    lines = ["📋 **Твой план по дням:**\n"]
    
    for date in sorted_dates:
        day_tasks = grouped[date]
        date_display = "📌 Без даты" if date == "no-date" else f"🗓 {format_date_ru(date)}"
        lines.append(f"\n{date_display}")
        lines.append("─" * 40)
        
        for t in day_tasks:
            emoji_imp = IMP_MAP.get(t.get("importance", "medium"), "📌")
            emoji_cat = {"study":"📚","home":"🏠","health":"💪","rest":"🎮","other":"📦"}.get(
                t.get("category", "other"), "📦"
            )
            duration = f"⏱ {t.get('duration_minutes', 0)} мин" if t.get("duration_minutes") else ""
            
            lines.append(f"• {emoji_imp} {emoji_cat} **{t['title']}** {duration}")
    
    return "\n".join(lines)