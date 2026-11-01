import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.auth_deps import get_current_user_dep
from app.database import get_db
from app.schemas import PlanRescueApplyRequest, PlanRescueProposal, PlanRescueRequest
from app.services.ai_service import AIServiceError
from app.services.rescue_service import apply_rescue_proposal, create_rescue_proposal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events/{event_id}/rescue", tags=["Plan Rescue AI (Signature Differentiator)"])


@router.post("/propose", response_model=PlanRescueProposal)
def propose_rescue_plan(
    event_id: str, rescue_req: PlanRescueRequest, current_user: dict = Depends(get_current_user_dep)
) -> PlanRescueProposal:
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
        raise HTTPException(status_code=500, detail=f"Plan Rescue proposal failed: {e!s}")


@router.post("/apply")
def apply_rescue_plan(
    event_id: str, apply_req: PlanRescueApplyRequest, current_user: dict = Depends(get_current_user_dep)
) -> dict[str, Any]:
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
        raise HTTPException(status_code=500, detail=f"Failed to apply Plan Rescue changes: {e!s}")


@router.get("/history")
def get_rescue_history(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> list[dict[str, Any]]:
    """Retrieves full audit log of all generated Plan Rescue proposals for this event."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Event not found")

        cursor.execute(
            """
        SELECT id, scenario_description, proposal_summary, applied, applied_at, created_at, full_proposal_json
        FROM plan_rescue_logs
        WHERE event_id = ?
        ORDER BY created_at DESC
        """,
            (event_id,),
        )

        logs = []
        for row in cursor.fetchall():
            d = dict(row)
            try:
                d["proposal_data"] = json.loads(d["full_proposal_json"])
            except Exception as exc:
                logger.warning("Could not decode proposal JSON in history: %s", exc)
                d["proposal_data"] = {}
            del d["full_proposal_json"]
            logs.append(d)

        return logs
