from typing import Any

from fastapi import Cookie, Header, HTTPException, status

from app.config import settings
from app.database import get_db
from app.routers.auth import get_current_user_from_db


def get_current_user_dep(
    gatherflow_session: str | None = Cookie(None), x_session_id: str | None = Header(None)
) -> dict[str, Any]:
    """
    Dependency that enforces valid authentication session on protected routes.
    Prioritizes secure HTTP-only cookies; allows X-Session-ID header in development / automated test runs.
    """
    token = gatherflow_session
    if not token and settings.ENVIRONMENT != "production":
        token = x_session_id

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication session required")

    user = get_current_user_from_db(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalid or expired")
    return user


def verify_event_ownership(event_id: str, user_id: str) -> dict[str, Any]:
    """
    Verifies that the requested event exists and is owned by the current authenticated user.
    Enforces strict user isolation across all event sub-resources (budget, tasks, vendors, AI rescue).
    Raises HTTP 404 if the event does not exist or belongs to another user.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
        return dict(row)
