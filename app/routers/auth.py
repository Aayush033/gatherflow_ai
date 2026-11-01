import secrets

from fastapi import APIRouter, Cookie, Header, HTTPException, Response, status

from app.config import settings
from app.database import get_db
from app.schemas import EvaluatorLoginRequest, UserOut

router = APIRouter(prefix="/api/auth", tags=["Authentication & User Isolation"])


def get_current_user_from_db(session_token: str) -> dict | None:
    if not session_token:
        return None
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE session_token = ?", (session_token,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_isolated_user(name: str = "Event Planner", email: str | None = None, role: str = "user") -> tuple[dict, str]:
    """Generates a cryptographically random session token and creates an isolated user record."""
    random_token = f"sess_{secrets.token_urlsafe(32)}"
    user_id = f"usr_{secrets.token_hex(8)}"
    user_email = email or f"planner_{secrets.token_hex(4)}@gatherflow.local"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (id, session_token, name, email) VALUES (?, ?, ?, ?)",
            (user_id, random_token, name, user_email),
        )
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = dict(cursor.fetchone())
        user["role"] = role
        return user, random_token


def apply_session_cookie(response: Response, session_token: str) -> None:
    """Sets secure HTTP-only session cookie."""
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME, value=session_token, httponly=True, samesite="lax", secure=is_prod, path="/"
    )


@router.get("/me", response_model=UserOut)
def get_current_user(
    response: Response, gatherflow_session: str | None = Cookie(None), x_session_id: str | None = Header(None)
) -> UserOut:
    """
    Returns the authenticated user for the current session.
    If no session exists, creates an isolated guest session with a secure server-generated token.
    """
    token = gatherflow_session
    # In development/test environments, allow X-Session-ID header fallback
    if not token and settings.ENVIRONMENT != "production":
        token = x_session_id

    user = get_current_user_from_db(token) if token else None

    if not user:
        # Create fresh isolated guest user with secure random server-generated token
        user, new_token = create_isolated_user(name="Guest Planner", role="guest")
        apply_session_cookie(response, new_token)
    else:
        user["role"] = "evaluator" if user.get("email") == settings.DEFAULT_EVALUATOR_EMAIL else "user"

    return UserOut(**user)


@router.post("/evaluator-login", response_model=UserOut)
def evaluator_login(req: EvaluatorLoginRequest, response: Response) -> UserOut:
    """
    Dedicated evaluator login. Requires server-validated passcode.
    Generates a cryptographically secure, random session token upon valid authentication.
    """
    # 1. Strictly validate passcode against server configuration
    if not req.passcode or req.passcode != settings.EVALUATOR_PASSCODE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid evaluator passcode")

    evaluator_email = settings.DEFAULT_EVALUATOR_EMAIL
    new_secure_token = f"sess_{secrets.token_urlsafe(32)}"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (evaluator_email,))
        user_row = cursor.fetchone()

        if not user_row:
            user_id = f"eval_{secrets.token_hex(6)}"
            cursor.execute(
                "INSERT INTO users (id, email, name, session_token) VALUES (?, ?, ?, ?)",
                (user_id, evaluator_email, settings.DEFAULT_EVALUATOR_NAME, new_secure_token),
            )
        else:
            user_id = user_row["id"]
            cursor.execute("UPDATE users SET session_token = ? WHERE id = ?", (new_secure_token, user_id))

        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = dict(cursor.fetchone())
        user["role"] = "evaluator"

    apply_session_cookie(response, new_secure_token)
    return UserOut(**user)


@router.post("/logout")
def logout(
    response: Response,
    gatherflow_session: str | None = Cookie(None),
    x_session_id: str | None = Header(None),
) -> dict[str, str]:
    """Clears the session cookie and revokes the active session token in persistent storage."""
    token = gatherflow_session or (x_session_id if settings.ENVIRONMENT != "production" else None)
    if token:
        with get_db() as conn:
            cursor = conn.cursor()
            revoked_placeholder = f"revoked_{secrets.token_hex(16)}"
            cursor.execute(
                "UPDATE users SET session_token = ? WHERE session_token = ?",
                (revoked_placeholder, token),
            )
    response.delete_cookie(key=settings.SESSION_COOKIE_NAME, path="/")
    return {"message": "Logged out successfully"}
