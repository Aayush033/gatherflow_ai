import time
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter
from app.config import settings
from app.database import get_db
from app.services.ai_service import check_model_health

router = APIRouter(prefix="/api/health", tags=["System Health & Diagnostics"])

_last_verified_cache = {
    "timestamp": 0.0,
    "result": None
}

class VerifyAiRequest(BaseModel):
    api_key: Optional[str] = None

@router.get("")
def get_system_health():
    """
    Returns system status including database integrity and AI configuration.
    Fast and non-blocking: does not trigger an expensive live external API call
    on every regular health check.
    """
    # 1. Database check
    db_status = "error"
    db_tables = []
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            db_tables = [r[0] for r in cursor.fetchall()]
            db_status = "healthy" if len(db_tables) >= 6 else "incomplete"
    except Exception as e:
        db_status = f"error: {str(e)}"
        
    # 2. AI configuration check (offline, instant)
    key_configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip())
    
    # If we have a recent verified result within 60s, use it; otherwise report configuration state
    cached = _last_verified_cache["result"]
    now = time.time()
    if cached and (now - _last_verified_cache["timestamp"] < 60.0):
        ai_info = cached
    else:
        ai_info = {
            "status": "configured" if key_configured else "unconfigured",
            "model": settings.GEMINI_MODEL,
            "connected": False,
            "key_configured": key_configured,
            "verified": False,
            "message": f"Gemini API key is configured for model {settings.GEMINI_MODEL}. Run /api/health/verify-ai to verify live connectivity." if key_configured else "GEMINI_API_KEY is not configured.",
            "verification_endpoint": "/api/health/verify-ai"
        }
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": {
            "status": db_status,
            "engine": "sqlite",
            "tables": db_tables
        },
        "ai": ai_info,
        "generative_ai": ai_info
    }

@router.post("/verify-ai")
def verify_ai_connectivity(req: Optional[VerifyAiRequest] = None):
    """
    Explicit, on-demand live connectivity check against the Gemini model.
    Sends a real smoke test request and caches the verified result.
    If an api_key is supplied in the request body, tests that specific key.
    """
    api_key_override = req.api_key.strip() if req and req.api_key else None
    result = check_model_health(api_key_override=api_key_override)
    if not api_key_override:
        _last_verified_cache["timestamp"] = time.time()
        _last_verified_cache["result"] = result
    
    return {
        "status": "healthy" if result.get("connected") else "degraded",
        "ai": result,
        "generative_ai": result
    }
