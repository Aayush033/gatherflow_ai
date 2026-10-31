from typing import Optional
from fastapi import Header, Cookie, HTTPException, status
from app.routers.auth import get_current_user_from_db
from app.config import settings

def get_current_user_dep(
    gatherflow_session: Optional[str] = Cookie(None),
    x_session_id: Optional[str] = Header(None)
) -> dict:
    """
    Dependency that enforces valid authentication session on protected routes.
    Prioritizes secure HTTP-only cookies; allows X-Session-ID header in development / automated test runs.
    """
    token = gatherflow_session
    if not token and settings.ENVIRONMENT != "production":
        token = x_session_id
        
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication session required"
        )
        
    user = get_current_user_from_db(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalid or expired"
        )
    return user
