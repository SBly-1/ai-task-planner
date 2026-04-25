from core.scheduler import build_plan

def test_sort_tasks():
    tasks = [
        {"title": "A", "importance": "low", "deadline": "2099-01-01", "status": "active"},
        {"title": "B", "importance": "high", "deadline": "2099-01-01", "status": "active"},
    ]
    sorted_tasks = build_plan(tasks)
    assert sorted_tasks[0]["importance"] == "high"
