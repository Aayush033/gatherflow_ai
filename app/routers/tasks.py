import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth_deps import get_current_user_dep, verify_event_ownership
from app.database import get_db
from app.schemas import TaskCreate, TaskOut, TaskSummaryOut, TaskUpdate
from app.services.task_service import compute_task_summary, evaluate_task

router = APIRouter(prefix="/api/events/{event_id}/tasks", tags=["Timeline & Task Management"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    event_id: str,
    status_filter: str | None = Query(None, alias="status"),
    category_filter: str | None = Query(None, alias="category"),
    current_user: dict = Depends(get_current_user_dep),
) -> list[TaskOut]:
    verify_event_ownership(event_id, current_user["id"])

    query = "SELECT * FROM tasks WHERE event_id = ?"
    params = [event_id]

    if status_filter:
        query += " AND status = ?"
        params.append(status_filter.lower())
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)

    query += " ORDER BY CASE WHEN status = 'completed' THEN 1 ELSE 0 END, due_date ASC NULLS LAST"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]

    results = []
    for task_row in rows:
        is_overdue, days_rem = evaluate_task(task_row)
        task_row["is_overdue"] = is_overdue
        task_row["days_remaining"] = days_rem
        results.append(TaskOut(**task_row))

    return results


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(event_id: str, task_in: TaskCreate, current_user: dict = Depends(get_current_user_dep)) -> TaskOut:
    verify_event_ownership(event_id, current_user["id"])
    task_id = f"task_{uuid.uuid4().hex[:8]}"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        INSERT INTO tasks (
            id, event_id, title, description, category, due_date,
            priority, status, assignee, dependency_task_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                task_id,
                event_id,
                task_in.title,
                task_in.description,
                task_in.category,
                task_in.due_date,
                task_in.priority,
                task_in.status,
                task_in.assignee,
                task_in.dependency_task_id,
                task_in.notes,
            ),
        )
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = dict(cursor.fetchone())

    is_overdue, days_rem = evaluate_task(row)
    row["is_overdue"] = is_overdue
    row["days_remaining"] = days_rem
    return TaskOut(**row)


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    event_id: str, task_id: str, task_update: TaskUpdate, current_user: dict = Depends(get_current_user_dep)
) -> TaskOut:
    verify_event_ownership(event_id, current_user["id"])
    update_data = task_update.model_dump(exclude_unset=True)

    with get_db() as conn:
        cursor = conn.cursor()
        if update_data:
            clauses = [f"{k} = ?" for k in update_data.keys()]
            clauses.append("updated_at = CURRENT_TIMESTAMP")
            values = list(update_data.values())
            values.extend([task_id, event_id])
            cursor.execute(f"UPDATE tasks SET {', '.join(clauses)} WHERE id = ? AND event_id = ?", values)
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Task not found")

        cursor.execute("SELECT * FROM tasks WHERE id = ? AND event_id = ?", (task_id, event_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        task_dict = dict(row)

    is_overdue, days_rem = evaluate_task(task_dict)
    task_dict["is_overdue"] = is_overdue
    task_dict["days_remaining"] = days_rem
    return TaskOut(**task_dict)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(event_id: str, task_id: str, current_user: dict = Depends(get_current_user_dep)) -> None:
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ? AND event_id = ?", (task_id, event_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Task not found")


@router.get("/summary", response_model=TaskSummaryOut)
def get_task_summary(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> TaskSummaryOut:
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE event_id = ?", (event_id,))
        rows = [dict(r) for r in cursor.fetchall()]
        return compute_task_summary(rows)
