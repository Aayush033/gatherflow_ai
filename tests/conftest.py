import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
import chromadb

from app.config import settings
from app.database import init_db
from app.main import app
from app.vector_db import set_chroma_client, init_vector_db
from app.schemas import EventPlanData, BudgetAllocationItem, TimelineMilestone, ChecklistItem

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Sets up isolated temporary SQLite and in-memory ChromaDB for tests.
    Guarantees that NO test vendors or test data pollute production databases.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = Path(tmp.name)
        
    settings.DATABASE_PATH = test_db_path
    settings.ENVIRONMENT = "test"
    init_db(test_db_path)
    
    # Use 100% in-memory ephemeral ChromaDB for tests
    ephemeral_client = chromadb.EphemeralClient()
    set_chroma_client(ephemeral_client)
    init_vector_db()
    
    yield test_db_path
    
    # Cleanup SQLite
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass

@pytest.fixture(autouse=True)
def mock_gemini_in_tests():
    """
    Prevents tests from making unintentional external network calls to Gemini.
    Provides realistic mock responses for automated test suites.
    """
    mock_plan = EventPlanData(
        concept="Mock Celebration Plan for Automated Testing",
        theme_details="Elegance and vibrant modern festive styling",
        budget_allocations=[
            BudgetAllocationItem(category="Venue", percentage=40.0, estimated_amount=120000.0, description="Grand Hall"),
            BudgetAllocationItem(category="Catering", percentage=30.0, estimated_amount=90000.0, description="Buffet Dinner"),
            BudgetAllocationItem(category="Decor", percentage=15.0, estimated_amount=45000.0, description="Floral setup"),
            BudgetAllocationItem(category="Photography", percentage=15.0, estimated_amount=45000.0, description="Candid photos")
        ],
        timeline_milestones=[
            TimelineMilestone(phase="Planning Phase", timeframe="T-60 days", description="Book core vendors"),
            TimelineMilestone(phase="Event Day", timeframe="T-0 days", description="Execute celebration schedule")
        ],
        suggested_checklist=[
            ChecklistItem(task="Confirm head caterer count", category="Catering", priority="high", suggested_days_before=14),
            ChecklistItem(task="Finalize sound playlist", category="Entertainment", priority="medium", suggested_days_before=7)
        ],
        vendor_categories=["Venue", "Catering", "Decor", "Photography"],
        risks=["Weather disruption", "Vendor delay"],
        contingencies=["Covered canopy on standby", "Pre-screen backup vendors"],
        next_actions=["Review budget allocations", "Assign task owners"]
    )
    
    with patch("app.services.ai_service.generate_initial_event_plan", return_value=mock_plan), \
         patch("app.services.ai_service.explain_budget_scenario_ai", return_value="Mock AI Strategic Advice: Focus on core hospitality and avoid last minute scope creep."), \
         patch("app.services.ai_service.copilot_chat_response", return_value={"reply": "Mock Copilot response.", "suggested_actions": ["Review budget"], "relevant_tab": "blueprint"}), \
         patch("app.services.ai_service.check_model_health", return_value={"status": "connected", "model": "gemini-3.8-flash", "connected": True, "key_configured": True, "message": "Verified mock connection."}):
        yield

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def test_user_headers(client):
    """Generates an authenticated session for user 1."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    token = resp.cookies.get(settings.SESSION_COOKIE_NAME)
    assert token is not None, "Session cookie must be set on response"
    return {
        "Cookie": f"{settings.SESSION_COOKIE_NAME}={token}",
        "X-Session-ID": token
    }

@pytest.fixture
def other_user_headers():
    """Generates an authenticated session for user 2 (strictly isolated)."""
    with TestClient(app) as second_client:
        resp = second_client.get("/api/auth/me")
        assert resp.status_code == 200
        token = resp.cookies.get(settings.SESSION_COOKIE_NAME)
        assert token is not None
        return {
            "Cookie": f"{settings.SESSION_COOKIE_NAME}={token}",
            "X-Session-ID": token
        }
