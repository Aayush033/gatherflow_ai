import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_deps import get_current_user_dep, verify_event_ownership
from app.database import get_db
from app.schemas import (
    BudgetItemCreate,
    BudgetItemOut,
    BudgetItemUpdate,
    BudgetScenarioRequest,
    BudgetScenarioResponse,
    BudgetSummaryOut,
)
from app.services import ai_service
from app.services.budget_service import (
    calculate_budget_scenario_deterministic,
    calculate_budget_summary,
)

router = APIRouter(prefix="/api/events/{event_id}/budget", tags=["Budget Intelligence Studio"])


@router.get("/items", response_model=list[BudgetItemOut])
def list_budget_items(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> list[BudgetItemOut]:
    """Retrieves all line-item budget allocations recorded for the specified event."""
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM budget_items WHERE event_id = ? ORDER BY category ASC, item_name ASC", (event_id,)
        )
        return [BudgetItemOut(**dict(r)) for r in cursor.fetchall()]


@router.post("/items", response_model=BudgetItemOut, status_code=status.HTTP_201_CREATED)
def create_budget_item(
    event_id: str, item_in: BudgetItemCreate, current_user: dict = Depends(get_current_user_dep)
) -> BudgetItemOut:
    """Creates a new discrete budget line item (estimated, quoted, committed, actual)."""
    verify_event_ownership(event_id, current_user["id"])
    item_id = f"bgt_{uuid.uuid4().hex[:8]}"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        INSERT INTO budget_items (
            id, event_id, category, item_name, estimated_amount,
            quoted_amount, committed_amount, actual_amount, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                item_id,
                event_id,
                item_in.category,
                item_in.item_name,
                item_in.estimated_amount,
                item_in.quoted_amount,
                item_in.committed_amount,
                item_in.actual_amount,
                item_in.status,
                item_in.notes,
            ),
        )
        cursor.execute("SELECT * FROM budget_items WHERE id = ?", (item_id,))
        return BudgetItemOut(**dict(cursor.fetchone()))


@router.patch("/items/{item_id}", response_model=BudgetItemOut)
def update_budget_item(
    event_id: str, item_id: str, item_update: BudgetItemUpdate, current_user: dict = Depends(get_current_user_dep)
) -> BudgetItemOut:
    """Updates an existing budget item's financial values or tracking status."""
    verify_event_ownership(event_id, current_user["id"])
    update_data = item_update.model_dump(exclude_unset=True)
    if not update_data:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM budget_items WHERE id = ? AND event_id = ?", (item_id, event_id))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Budget item not found")
            return BudgetItemOut(**dict(row))

    with get_db() as conn:
        cursor = conn.cursor()
        clauses = [f"{k} = ?" for k in update_data.keys()]
        clauses.append("updated_at = CURRENT_TIMESTAMP")
        values = list(update_data.values())
        values.extend([item_id, event_id])

        cursor.execute(f"UPDATE budget_items SET {', '.join(clauses)} WHERE id = ? AND event_id = ?", values)
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Budget item not found")

        cursor.execute("SELECT * FROM budget_items WHERE id = ?", (item_id,))
        return BudgetItemOut(**dict(cursor.fetchone()))


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_item(event_id: str, item_id: str, current_user: dict = Depends(get_current_user_dep)) -> None:
    """Deletes a budget line item from the persistent database."""
    verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM budget_items WHERE id = ? AND event_id = ?", (item_id, event_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Budget item not found")


@router.get("/summary", response_model=BudgetSummaryOut)
def get_budget_summary(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> BudgetSummaryOut:
    """Computes deterministic budget aggregations, variance, and tier breakdowns."""
    event = verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_items WHERE event_id = ?", (event_id,))
        items = [dict(r) for r in cursor.fetchall()]
        return calculate_budget_summary(event["budget"], event["currency"], items)


@router.post("/scenario", response_model=BudgetScenarioResponse)
def analyze_budget_scenario(
    event_id: str, scenario: BudgetScenarioRequest, current_user: dict = Depends(get_current_user_dep)
) -> BudgetScenarioResponse:
    """
    Runs a 'What-If' scenario. Calculates numerical impact deterministically,
    and asks Gemini to explain strategic trade-offs and alternatives.
    """
    event = verify_event_ownership(event_id, current_user["id"])
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM budget_items WHERE event_id = ?", (event_id,))
        items = [dict(r) for r in cursor.fetchall()]
        summary = calculate_budget_summary(event["budget"], event["currency"], items)

    # 1. Deterministic arithmetic calculation
    calc = calculate_budget_scenario_deterministic(
        current_budget=event["budget"],
        current_guest_count=event["guest_count"],
        total_committed=summary.total_committed,
        scenario=scenario,
        currency=event["currency"],
    )

    # 2. Strategic qualitative analysis via Gemini
    ai_advice = ai_service.explain_budget_scenario_ai(
        event_data=event, deterministic_analysis=calc["deterministic_analysis"], scenario_notes=scenario.notes
    )

    return BudgetScenarioResponse(
        original_budget=calc["original_budget"],
        projected_budget=calc["projected_budget"],
        original_guest_count=calc["original_guest_count"],
        projected_guest_count=calc["projected_guest_count"],
        projected_cost_impact=calc["projected_cost_impact"],
        projected_variance=calc["projected_variance"],
        is_feasible=calc["is_feasible"],
        deterministic_analysis=calc["deterministic_analysis"],
        ai_tradeoff_advice=ai_advice,
    )
