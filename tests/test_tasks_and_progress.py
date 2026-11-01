from datetime import date

from app.services.task_service import compute_task_summary, evaluate_task


def test_task_overdue_logic():
    """
    Verifies that:
    1. Past due tasks in 'todo' or 'in_progress' are marked overdue.
    2. Future tasks are NOT overdue.
    3. Completed tasks are NEVER overdue, even if their due date is in the past.
    """
    today = date(2026, 10, 20)

    # 1. Past due, todo
    task_past_todo = {"status": "todo", "due_date": "2026-10-10"}
    is_od, days = evaluate_task(task_past_todo, today)
    assert is_od is True
    assert days == -10

    # 2. Future due, todo
    task_future_todo = {"status": "todo", "due_date": "2026-10-25"}
    is_od, days = evaluate_task(task_future_todo, today)
    assert is_od is False
    assert days == 5

    # 3. Past due, BUT completed -> Must NOT be overdue
    task_past_completed = {"status": "completed", "due_date": "2026-10-01"}
    is_od, days = evaluate_task(task_past_completed, today)
    assert is_od is False
    assert days == -19


def test_progress_percentage_calculation():
    """
    Verifies that progress percentage is calculated deterministically
    from completed vs total tasks. Never fabricated.
    """
    tasks = [
        {"status": "completed", "due_date": "2026-10-10"},
        {"status": "completed", "due_date": "2026-10-12"},
        {"status": "in_progress", "due_date": "2026-10-22"},
        {"status": "todo", "due_date": "2026-10-30"},
    ]

    summary = compute_task_summary(tasks, date(2026, 10, 20))
    assert summary.total_tasks == 4
    assert summary.completed_tasks == 2
    assert summary.in_progress_tasks == 1
    assert summary.todo_tasks == 1
    assert summary.overdue_tasks == 0
    assert summary.progress_percentage == 50.0  # (2 / 4) * 100


def test_empty_tasks_progress():
    summary = compute_task_summary([])
    assert summary.total_tasks == 0
    assert summary.progress_percentage == 0.0
