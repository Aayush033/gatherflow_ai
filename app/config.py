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

    def __init__(self) -> None:
        self.BASE_DIR: Path = BASE_DIR
        self.DATABASE_PATH: Path = BASE_DIR / "gatherflow.db"
        self._database_url: str | None = os.getenv("DATABASE_URL")
        self.CHROMA_PERSIST_PATH: Path = BASE_DIR / "chroma_db"

        # AI Configuration (Gemini)
        self.GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
        # Default model as specified by the master challenge: gemini-3.8-flash
        self.GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

        # Environment
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")

        # Security & Evaluator Session
        self.SESSION_COOKIE_NAME: str = "gatherflow_session"
        self.SESSION_SECRET_KEY: str = os.getenv(
            "SESSION_SECRET_KEY", "gatherflow-default-session-secret-change-in-prod"
        )
        self.EVALUATOR_PASSCODE: str = os.getenv("EVALUATOR_PASSCODE", "gatherflow-evaluator")
        self.DEFAULT_EVALUATOR_EMAIL: str = "evaluator@gatherflow.local"
        self.DEFAULT_EVALUATOR_NAME: str = "Auditor & Evaluator"

    @property
    def DATABASE_URL(self) -> str:
        if self._database_url:
            return self._database_url
        return f"sqlite:///{self.DATABASE_PATH}"

    @DATABASE_URL.setter
    def DATABASE_URL(self, value: str | None) -> None:
        self._database_url = value


settings = Settings()
