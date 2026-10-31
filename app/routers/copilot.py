import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth_deps import get_current_user_dep
from app.schemas import CopilotMessage, CopilotResponse
from app.services.budget_service import calculate_budget_summary
from app.services.task_service import evaluate_task
from app.services import ai_service
from app.services.ai_service import AIServiceError

router = APIRouter(prefix="/api/events/{event_id}/copilot", tags=["Generative AI Event Copilot"])

def verify_event_ownership(event_id: str, user_id: str) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")
        return dict(row)

@router.get("/history")
def get_chat_history(
    event_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, role, content, created_at FROM copilot_messages WHERE event_id = ? ORDER BY created_at ASC",
            (event_id,)
        )
        return [dict(r) for r in cursor.fetchall()]

@router.post("/chat", response_model=CopilotResponse)
def chat_with_copilot(
    event_id: str,
    msg_in: CopilotMessage,
    current_user: dict = Depends(get_current_user_dep)
):
    event = verify_event_ownership(event_id, current_user["id"])
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Fetch budget
        cursor.execute("SELECT * FROM budget_items WHERE event_id = ?", (event_id,))
        budget_items = [dict(r) for r in cursor.fetchall()]
        budget_summary = calculate_budget_summary(event["budget"], event["currency"], budget_items).model_dump()
        
        # 2. Fetch tasks
        cursor.execute("SELECT * FROM tasks WHERE event_id = ?", (event_id,))
        tasks = [dict(r) for r in cursor.fetchall()]
        for t in tasks:
            is_overdue, days_rem = evaluate_task(t)
            t["is_overdue"] = is_overdue
            t["days_remaining"] = days_rem
            
        # 3. Fetch vendors
        cursor.execute("SELECT * FROM vendors WHERE event_id = ?", (event_id,))
        vendors = [dict(r) for r in cursor.fetchall()]
        
        # 4. Fetch recent chat history
        cursor.execute(
            "SELECT role, content FROM copilot_messages WHERE event_id = ? ORDER BY created_at ASC LIMIT 10",
            (event_id,)
        )
        history = [dict(r) for r in cursor.fetchall()]
        
        # Save user message
        user_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO copilot_messages (id, event_id, role, content)
        VALUES (?, ?, 'user', ?)
        """, (user_msg_id, event_id, msg_in.message))

    # 5. ChromaDB RAG Vector Retrieval
    rag_knowledge = []
    rag_vendors = []
    try:
        from app.vector_db import search_knowledge_semantic, search_vendors_semantic
        rag_knowledge = search_knowledge_semantic(msg_in.message, n_results=2)
        rag_vendors = search_vendors_semantic(msg_in.message, n_results=2)
    except Exception:
        pass

    # 6. Call Gemini
    try:
        copilot_result = ai_service.copilot_chat_response(
            event_data=event,
            budget_summary=budget_summary,
            tasks=tasks,
            vendors=vendors,
            chat_history=history,
            user_message=msg_in.message,
            rag_knowledge=rag_knowledge,
            rag_vendors=rag_vendors
        )
    except AIServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Copilot inference failed: {str(e)}")

    # 6. Save assistant response
    with get_db() as conn:
        cursor = conn.cursor()
        asst_msg_id = f"msg_{uuid.uuid4().hex[:8]}"
        cursor.execute("""
        INSERT INTO copilot_messages (id, event_id, role, content)
        VALUES (?, ?, 'assistant', ?)
        """, (asst_msg_id, event_id, copilot_result["reply"]))

    return CopilotResponse(**copilot_result)
