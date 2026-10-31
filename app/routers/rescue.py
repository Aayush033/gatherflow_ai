import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth_deps import get_current_user_dep
from app.schemas import (
    PlanRescueRequest,
    PlanRescueProposal,
    PlanRescueApplyRequest
)
from app.services.rescue_service import create_rescue_proposal, apply_rescue_proposal
from app.services.ai_service import AIServiceError

router = APIRouter(prefix="/api/events/{event_id}/rescue", tags=["Plan Rescue AI (Signature Differentiator)"])

@router.post("/propose", response_model=PlanRescueProposal)
def propose_rescue_plan(
    event_id: str,
    rescue_req: PlanRescueRequest,
    current_user: dict = Depends(get_current_user_dep)
):
    """
    Signature replanning workflow:
    1. Collects live stored event, budget, tasks, and vendors.
    2. Sends context + disruption scenario to Gemini.
    3. Produces a reviewable proposal with trade-offs, facts vs assumptions,
       and proposed budget/task modifications.
    4. Does NOT automatically change records until explicit user approval.
    """
    try:
        proposal = create_rescue_proposal(event_id, rescue_req, current_user["id"])
        return PlanRescueProposal(**proposal)
    except AIServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan Rescue proposal failed: {str(e)}")

@router.post("/apply")
def apply_rescue_plan(
    event_id: str,
    apply_req: PlanRescueApplyRequest,
    current_user: dict = Depends(get_current_user_dep)
):
    """
    Applies only user-approved modifications to persistent database records.
    Recalculates totals and maintains an audit log.
    """
    try:
        result = apply_rescue_proposal(event_id, apply_req, current_user["id"])
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to apply Plan Rescue changes: {str(e)}")

@router.get("/history")
def get_rescue_history(
    event_id: str,
    current_user: dict = Depends(get_current_user_dep)
):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Event not found")
            
        cursor.execute("""
        SELECT id, scenario_description, proposal_summary, applied, applied_at, created_at, full_proposal_json
        FROM plan_rescue_logs
        WHERE event_id = ?
        ORDER BY created_at DESC
        """, (event_id,))
        
        logs = []
        for row in cursor.fetchall():
            d = dict(row)
            try:
                d["proposal_data"] = json.loads(d["full_proposal_json"])
            except Exception:
                d["proposal_data"] = {}
            del d["full_proposal_json"]
            logs.append(d)
            
        return logs
