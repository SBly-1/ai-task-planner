CAT_MAP = {
    "study": "учёба",
    "home": "быт",
    "health": "здоровье",
    "rest": "отдых",
    "other": "другое",
}

IMP_MAP = {
    "high": "🔥 высокая",
    "medium": "⚡ средняя",
    "low": "🌱 низкая",
}


def format_plan(tasks: list[dict]) -> str:
    if not tasks:
        return "📋 План пуст."

    lines = ["📋 **План по приоритету:**\n"]

    for index, task in enumerate(tasks, start=1):
        title = task.get("title", "Без названия")
        importance = IMP_MAP.get(task.get("importance", "low"), "🌱 низкая")
        category = CAT_MAP.get(task.get("category", "other"), "другое")
        deadline = task.get("deadline", "не указан")
        duration = task.get("duration_minutes", 0)

        lines.append(
            f"{index}. **{title}**\n"
            f"   • важность: {importance}\n"
            f"   • категория: {category}\n"
            f"   • дедлайн: {deadline}\n"
            f"   • длительность: {duration} мин\n"
        )

    return "\n".join(lines)
