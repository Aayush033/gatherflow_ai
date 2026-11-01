import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    PROJECT_NAME: str = "GatherFlow AI"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "GenAI-powered planning studio for weddings, birthdays, and community events"

    # Database
    DATABASE_PATH: Path = BASE_DIR / "gatherflow.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")
    CHROMA_PERSIST_PATH: Path = BASE_DIR / "chroma_db"

    # AI Configuration (Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # Default model as specified by the master challenge: gemini-3.8-flash
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")

    # Security & Evaluator Session
    SESSION_COOKIE_NAME: str = "gatherflow_session"
    SESSION_SECRET_KEY: str = os.getenv("SESSION_SECRET_KEY", "gatherflow-default-session-secret-change-in-prod")
    EVALUATOR_PASSCODE: str = os.getenv("EVALUATOR_PASSCODE", "gatherflow-evaluator")
    DEFAULT_EVALUATOR_EMAIL: str = "evaluator@gatherflow.local"
    DEFAULT_EVALUATOR_NAME: str = "Auditor & Evaluator"


settings = Settings()
