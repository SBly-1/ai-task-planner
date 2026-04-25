from utils.validation import (
    validate_category,
    validate_deadline,
    validate_duration,
    validate_importance,
)

def test_validate_date_valid():
    assert validate_deadline("2026-05-20") == []

def test_validate_date_invalid_format():
    assert validate_deadline("20-05-2026")

def test_validate_priority_valid():
    assert validate_importance("normal") == []

def test_validate_priority_invalid():
    assert validate_importance("super-high")

def test_validate_duration_invalid():
    assert validate_duration(0)

def test_validate_category_valid():
    assert validate_category("study") == []
