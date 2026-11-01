from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import BASE_DIR, settings
from app.database import init_db
from app.routers import (
    auth,
    blueprint,
    budget,
    copilot,
    events,
    health,
    rescue,
    tasks,
    vendors,
)
from app.services.ai_service import check_model_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME, version=settings.VERSION, description=settings.DESCRIPTION, lifespan=lifespan
)

# CORS configuration — restricted to trusted origins (same-origin app + dev origins)
allowed_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
if settings.ALLOWED_ORIGINS:
    for orig in settings.ALLOWED_ORIGINS.split(","):
        if orig.strip():
            allowed_origins.append(orig.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Session-ID", "Authorization"],
)

# Register API Routers
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(blueprint.router)
app.include_router(budget.router)
app.include_router(tasks.router)
app.include_router(vendors.router)
app.include_router(rescue.router)
app.include_router(copilot.router)
app.include_router(health.router)


class SetApiKeyRequest(BaseModel):
    api_key: str
    model: str | None = None


@app.post("/api/config/gemini-key", tags=["Configuration"])
def configure_gemini_key(req: SetApiKeyRequest) -> dict[str, Any]:
    """
    Development-only endpoint for configuring Gemini credentials.
    Strictly blocked in production environments.
    """
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Runtime API key configuration is disabled in production. Configure GEMINI_API_KEY via server environment variables.",
        )

    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    settings.GEMINI_API_KEY = req.api_key.strip()
    if req.model and req.model.strip():
        settings.GEMINI_MODEL = req.model.strip()

    health_result = check_model_health(api_key_override=settings.GEMINI_API_KEY)
    return {"success": health_result.get("connected", False), "health": health_result}


# Mount static directory for the frontend
static_dir = BASE_DIR / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", include_in_schema=False, response_model=None)
async def serve_index() -> FileResponse | JSONResponse:
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        {
            "message": f"Welcome to {settings.PROJECT_NAME} API v{settings.VERSION}. Frontend static files are initializing.",
            "api_docs": "/docs",
            "health": "/api/health",
        }
    )
