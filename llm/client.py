import json
import re
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from config import LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, OPENAI_MODEL
from llm.prompts import TASK_EXTRACTION_PROMPT


load_dotenv()


def get_llm():
    if LLM_PROVIDER == "openai":
        return ChatOpenAI(model=OPENAI_MODEL, temperature=0.1)

    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.1,
    )


def _strip_code_fence(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    return text


def _extract_json(text: str) -> dict[str, Any] | None:
    text = _strip_code_fence(text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _normalize_deadline(raw: str) -> str | None:
    text = raw.lower()
    today = datetime.now().date()

    if "послезавтра" in text:
        return (today + timedelta(days=2)).isoformat()

    if "завтра" in text:
        return (today + timedelta(days=1)).isoformat()

    if "сегодня" in text:
        return today.isoformat()

    iso_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if iso_match:
        return iso_match.group(1)

    ru_date_match = re.search(r"\b(\d{1,2})[./](\d{1,2})(?:[./](20\d{2}))?\b", text)
    if ru_date_match:
        day = int(ru_date_match.group(1))
        month = int(ru_date_match.group(2))
        year = int(ru_date_match.group(3)) if ru_date_match.group(3) else today.year

        try:
            return datetime(year, month, day).date().isoformat()
        except ValueError:
            return None

    return None


def _extract_duration(raw: str) -> int | None:
    text = raw.lower()

    hours_match = re.search(r"(\d+)\s*(час|часа|часов|ч)\b", text)
    minutes_match = re.search(r"(\d+)\s*(мин|минут|минуты|м)\b", text)

    total = 0

    if hours_match:
        total += int(hours_match.group(1)) * 60

    if minutes_match:
        total += int(minutes_match.group(1))

    if total > 0:
        return total

    if re.fullmatch(r"\s*\d{1,2}\s*", text):
        return int(text) * 60

    return None


def _extract_importance(raw: str) -> str | None:
    text = raw.lower()

    if any(word in text for word in ["срочно", "важно", "важная", "важный", "high"]):
        return "high"

    if any(word in text for word in ["средне", "средняя", "обычно", "medium"]):
        return "medium"

    if any(word in text for word in ["низкая", "низкий", "неважно", "low", "можно потом"]):
        return "low"

    return None


def _extract_category(raw: str) -> str | None:
    text = raw.lower()

    if any(word in text for word in ["учеб", "учёб", "лаба", "лаборатор", "дз", "экзамен", "веб", "алгебр", "study"]):
        return "study"

    if any(word in text for word in ["купить", "магазин", "продукт", "уборк", "дом", "home"]):
        return "home"

    if any(word in text for word in ["спорт", "трен", "бег", "зал", "здоров", "health"]):
        return "health"

    if any(word in text for word in ["отдых", "сон", "фильм", "погулять", "rest"]):
        return "rest"

    if "other" in text or "другое" in text:
        return "other"

    return None


def _looks_like_greeting(raw: str) -> bool:
    text = raw.lower().strip()
    return text in {
        "привет",
        "здравствуй",
        "здравствуйте",
        "добрый день",
        "доброе утро",
        "добрый вечер",
        "hi",
        "hello",
    }


def _looks_like_help(raw: str) -> bool:
    text = raw.lower()
    return any(word in text for word in ["помощь", "подсказка", "что ты умеешь", "как пользоваться", "help"])


def _looks_like_show_plan(raw: str) -> bool:
    text = raw.lower()
    return any(word in text for word in ["план", "список задач", "покажи задачи", "расписание"])


def _looks_like_complete(raw: str) -> bool:
    text = raw.lower()
    return any(word in text for word in ["выполн", "готово", "сделал", "сделала", "done"])


def _looks_like_postpone(raw: str) -> bool:
    text = raw.lower()
    return any(word in text for word in ["перенес", "перенести", "отлож", "потом", "postpone"])


def _clean_title(raw: str) -> str | None:
    text = raw.strip()

    if not text:
        return None

    if (
        _extract_duration(text)
        or _normalize_deadline(text)
        or _extract_importance(text)
        or _extract_category(text)
    ) and len(text.split()) <= 3:
        return None

    patterns = [
        r"\bсегодня\b",
        r"\bзавтра\b",
        r"\bпослезавтра\b",
        r"\b20\d{2}-\d{2}-\d{2}\b",
        r"\b\d{1,2}[./]\d{1,2}(?:[./]20\d{2})?\b",
        r"\b\d+\s*(час|часа|часов|ч)\b",
        r"\b\d+\s*(мин|минут|минуты|м)\b",
        r"\b(high|medium|low)\b",
        r"\bважно\b",
        r"\bсрочно\b",
        r"\bсредняя\b",
        r"\bнизкая\b",
        r"\bstudy\b",
        r"\bhome\b",
        r"\bhealth\b",
        r"\brest\b",
        r"\bother\b",
    ]

    for pattern in patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text).strip(" ,.-")

    return text or None


def _heuristic_parse(user_message: str, state: dict | None = None) -> dict:
    state = state or {}

    if _looks_like_greeting(user_message) or _looks_like_help(user_message):
        return {"intent": "help", "task_data": {}}

    if _looks_like_show_plan(user_message):
        return {"intent": "show_plan", "task_data": {}}

    if _looks_like_complete(user_message):
        return {"intent": "complete_task", "task_data": {}}

    if _looks_like_postpone(user_message):
        return {"intent": "postpone_task", "task_data": {}}

    task_data: dict[str, Any] = {}

    deadline = _normalize_deadline(user_message)
    duration = _extract_duration(user_message)
    importance = _extract_importance(user_message)
    category = _extract_category(user_message)
    title = _clean_title(user_message)

    if deadline:
        task_data["deadline"] = deadline

    if duration:
        task_data["duration_minutes"] = duration

    if importance:
        task_data["importance"] = importance

    if category:
        task_data["category"] = category

    if title:
        task_data["title"] = title

    return {"intent": "add_task", "task_data": task_data}


def _merge_task_data(base: dict, extra: dict) -> dict:
    result = dict(base or {})

    for key, value in (extra or {}).items():
        if value not in (None, "", [], {}):
            result[key] = value

    return result


def parse_user_message(user_message: str, state: dict | None = None) -> dict:
    state = state or {}
    heuristic_result = _heuristic_parse(user_message, state)

    if heuristic_result["intent"] != "add_task":
        return heuristic_result

    llm_result = {"intent": "add_task", "task_data": {}}

    try:
        llm = get_llm()
        prompt = TASK_EXTRACTION_PROMPT.format(
            today=datetime.now().date().isoformat(),
            draft_task=json.dumps(state.get("draft_task", {}), ensure_ascii=False),
            missing_fields=json.dumps(state.get("missing_fields", []), ensure_ascii=False),
            user_message=user_message,
        )
        response = llm.invoke(prompt)
        parsed = _extract_json(response.content)

        if isinstance(parsed, dict):
            llm_result["intent"] = parsed.get("intent") or "add_task"
            llm_result["task_data"] = parsed.get("task_data") or {}
    except Exception:
        llm_result = {"intent": "add_task", "task_data": {}}

    if llm_result["intent"] != "add_task":
        return llm_result

    return {
        "intent": "add_task",
        "task_data": _merge_task_data(
            llm_result.get("task_data", {}),
            heuristic_result.get("task_data", {}),
        ),
    }
