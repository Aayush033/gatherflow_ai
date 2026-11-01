from datetime import date, datetime
from typing import Any

from app.schemas import TaskSummaryOut


def parse_date(date_str: str | None) -> date | None:
    """Safely parses an ISO date string (YYYY-MM-DD) into a date object, returning None on failure."""
    if not date_str:
        return None
    try:
        # Handle YYYY-MM-DD
        return datetime.strptime(date_str[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def evaluate_task(task_row: dict[str, Any], today: date | None = None) -> tuple[bool, int | None]:
    """
    Evaluates whether a task is overdue and calculates days remaining.
    A completed task is NEVER considered overdue.
    """
    if today is None:
        today = date.today()

    status = (task_row.get("status") or "").lower()
    due_date = parse_date(task_row.get("due_date"))

    if not due_date:
        return False, None

    delta = (due_date - today).days

    if status == "completed":
        return False, delta

    is_overdue = delta < 0
    return is_overdue, delta


def compute_task_summary(tasks: list[dict[str, Any]], today: date | None = None) -> TaskSummaryOut:
    """
    Calculates genuine task progress metrics from actual saved task records.
    Never invents progress percentages.
    """
    if today is None:
        today = date.today()

    total_tasks = len(tasks)
    if total_tasks == 0:
        return TaskSummaryOut(
            total_tasks=0,
            completed_tasks=0,
            in_progress_tasks=0,
            todo_tasks=0,
            overdue_tasks=0,
            progress_percentage=0.0,
        )

    completed_tasks = 0
    in_progress_tasks = 0
    todo_tasks = 0
    overdue_tasks = 0

    for task_item in tasks:
        status = (task_item.get("status") or "todo").lower()
        is_overdue, _ = evaluate_task(task_item, today)

        if status == "completed":
            completed_tasks += 1
        elif status == "in_progress":
            in_progress_tasks += 1
        else:
            todo_tasks += 1

        if is_overdue:
            overdue_tasks += 1

    progress_percentage = round((completed_tasks / total_tasks) * 100.0, 1)

    return TaskSummaryOut(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        in_progress_tasks=in_progress_tasks,
        todo_tasks=todo_tasks,
        overdue_tasks=overdue_tasks,
        progress_percentage=progress_percentage,
    )
