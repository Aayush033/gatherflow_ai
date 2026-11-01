import json
import logging
import uuid
from datetime import datetime
from typing import Any

from app.database import get_db
from app.schemas import (
    PlanRescueApplyRequest,
    PlanRescueRequest,
)
from app.services.ai_service import generate_plan_rescue_proposal
from app.services.budget_service import calculate_budget_summary
from app.services.task_service import evaluate_task

logger = logging.getLogger(__name__)


def create_rescue_proposal(event_id: str, request: PlanRescueRequest, user_id: str) -> dict[str, Any]:
    """
    Retrieves the actual saved event, budget, task, and vendor context,
    calls Gemini to generate a contextual replanning proposal,
    and stores it in the rescue audit log awaiting user review.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Verify ownership & fetch event
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        event = cursor.fetchone()
        if not event:
            raise ValueError("Event not found or access denied")
        event_dict = dict(event)

        # Fetch budget items
        cursor.execute("SELECT * FROM budget_items WHERE event_id = ?", (event_id,))
        budget_rows = [dict(r) for r in cursor.fetchall()]
        budget_summary = calculate_budget_summary(event_dict["budget"], event_dict["currency"], budget_rows)
        budget_summary_dict = budget_summary.model_dump()
        budget_summary_dict["items"] = budget_rows

        # Fetch tasks
        cursor.execute("SELECT * FROM tasks WHERE event_id = ? ORDER BY due_date ASC", (event_id,))
        task_rows = [dict(r) for r in cursor.fetchall()]
        for t in task_rows:
            is_overdue, days_rem = evaluate_task(t)
            t["is_overdue"] = is_overdue
            t["days_remaining"] = days_rem

        # Fetch vendors
        cursor.execute("SELECT * FROM vendors WHERE event_id = ?", (event_id,))
        vendor_rows = [dict(r) for r in cursor.fetchall()]

        # Retrieve ChromaDB contingency playbooks
        playbooks = []
        try:
            from app.vector_db import search_rescue_playbooks

            playbooks = search_rescue_playbooks(f"{request.scenario_type}: {request.description}", n_results=2)
        except Exception as exc:
            logger.debug("Playbook retrieval omitted in test/offline environment: %s", exc)

        # Generate proposal with Gemini
        proposal_data = generate_plan_rescue_proposal(
            event_data=event_dict,
            budget_summary=budget_summary_dict,
            tasks=task_rows,
            vendors=vendor_rows,
            scenario=request,
            playbooks=playbooks,
        )

        rescue_id = f"rescue_{uuid.uuid4().hex[:10]}"
        proposal_data["rescue_id"] = rescue_id
        if "confirmed_facts" not in proposal_data or not proposal_data["confirmed_facts"]:
            proposal_data["confirmed_facts"] = [
                f"Event: {event_dict.get('title')}",
                f"Budget: {event_dict.get('currency')} {event_dict.get('budget'):,.2f}",
                f"Guest Count: {event_dict.get('guest_count')}",
            ]

        # Store in plan_rescue_logs
        cursor.execute(
            """
        INSERT INTO plan_rescue_logs (id, event_id, scenario_description, proposal_summary, full_proposal_json, applied)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
            (
                rescue_id,
                event_id,
                f"[{request.scenario_type}] {request.description}",
                proposal_data.get("situation_summary", "Plan Rescue Replanning Proposal"),
                json.dumps(proposal_data),
            ),
        )

        return proposal_data


def _apply_event_parameter_updates(
    cursor: Any,
    event_id: str,
    user_id: str,
    event_dict: dict[str, Any],
    updates: dict[str, Any],
    applied_actions: list[str],
) -> None:
    """Applies event-level adjustments (budget, guest count, date) within the transaction."""
    new_budget = updates.get("budget")
    new_guests = updates.get("guest_count")
    new_date = updates.get("date")

    update_clauses = []
    update_params = []

    if new_budget is not None:
        val = float(new_budget)
        if val <= 0:
            raise ValueError(f"Invalid proposed budget: {val}. Budget must be greater than zero.")
        update_clauses.append("budget = ?")
        update_params.append(val)
        applied_actions.append(f"Updated event budget to {event_dict['currency']} {val:,.2f}")

    if new_guests is not None:
        g_val = int(new_guests)
        if g_val <= 0 or g_val > 100000:
            raise ValueError(f"Invalid proposed guest count: {g_val}.")
        update_clauses.append("guest_count = ?")
        update_params.append(g_val)
        applied_actions.append(f"Updated guest count to {g_val}")

    if new_date and len(str(new_date).strip()) >= 10:
        d_str = str(new_date).strip()[:10]
        try:
            datetime.strptime(d_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid proposed event date format: {d_str}. Expected YYYY-MM-DD.")
        update_clauses.append("date = ?")
        update_params.append(d_str)
        applied_actions.append(f"Updated event date to {d_str}")

    if update_clauses:
        update_clauses.append("updated_at = CURRENT_TIMESTAMP")
        update_params.extend([event_id, user_id])
        query = f"UPDATE events SET {', '.join(update_clauses)} WHERE id = ? AND user_id = ?"
        cursor.execute(query, update_params)


def _apply_budget_adjustments(
    cursor: Any,
    event_id: str,
    adjustments: list[dict[str, Any]],
    applied_actions: list[str],
) -> None:
    """Applies line-item budget adjustments or inserts new items if absent."""
    for b_adj in adjustments:
        cat = b_adj.get("category", "General")
        item_name = b_adj.get("item_name", "Adjusted Item")
        proposed_est = max(0.0, float(b_adj.get("proposed_estimate", 0.0)))
        reason = b_adj.get("adjustment_reason", "")

        cursor.execute(
            "SELECT id FROM budget_items WHERE event_id = ? AND (LOWER(item_name) = LOWER(?) OR LOWER(category) = LOWER(?)) LIMIT 1",
            (event_id, item_name, cat),
        )
        existing = cursor.fetchone()

        if existing:
            cursor.execute(
                """
                UPDATE budget_items
                SET estimated_amount = ?, notes = coalesce(notes || ' | ', '') || ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND event_id = ?
                """,
                (proposed_est, f"Plan Rescue: {reason}", existing["id"], event_id),
            )
            applied_actions.append(f"Adjusted budget for '{item_name}' to {proposed_est:,.2f}")
        else:
            new_item_id = f"bgt_{uuid.uuid4().hex[:8]}"
            cursor.execute(
                """
                INSERT INTO budget_items (id, event_id, category, item_name, estimated_amount, status, notes)
                VALUES (?, ?, ?, ?, ?, 'planned', ?)
                """,
                (new_item_id, event_id, cat, item_name, proposed_est, f"Added by Plan Rescue: {reason}"),
            )
            applied_actions.append(f"Added new budget item '{item_name}' ({proposed_est:,.2f})")


def _apply_task_actions(
    cursor: Any,
    event_id: str,
    actions: list[dict[str, Any]],
    applied_actions: list[str],
) -> None:
    """Creates emergency tasks or elevates priorities for existing tasks."""
    for t_act in actions:
        action = (t_act.get("action") or "add").lower()
        title = t_act.get("title")
        cat = t_act.get("category", "General")
        priority = t_act.get("priority", "high")
        notes = t_act.get("notes") or "Created by Plan Rescue"

        if action == "add":
            task_id = f"task_{uuid.uuid4().hex[:8]}"
            cursor.execute(
                """
                INSERT INTO tasks (id, event_id, title, category, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, 'todo', ?)
                """,
                (task_id, event_id, title, cat, priority, notes),
            )
            applied_actions.append(f"Created emergency task '{title}'")
        elif action == "modify":
            cursor.execute(
                """
                UPDATE tasks
                SET priority = ?, notes = coalesce(notes || ' | ', '') || ?, updated_at = CURRENT_TIMESTAMP
                WHERE event_id = ? AND LOWER(title) LIKE LOWER(?)
                """,
                (priority, notes, event_id, f"%{title}%"),
            )
            if cursor.rowcount > 0:
                applied_actions.append(f"Updated priority for task '{title}' to {priority}")
            else:
                fallback_id = f"task_{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    """
                    INSERT INTO tasks (id, event_id, title, category, priority, status, notes)
                    VALUES (?, ?, ?, ?, ?, 'todo', ?)
                    """,
                    (fallback_id, event_id, title, cat, priority, f"{notes} (created by Plan Rescue)"),
                )
                applied_actions.append(f"Created emergency task '{title}' with priority {priority}")


def apply_rescue_proposal(event_id: str, request: PlanRescueApplyRequest, user_id: str) -> dict[str, Any]:
    """
    Applies the approved Plan Rescue adjustments to persistent database records.
    Modifies only what the user has explicitly approved.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Verify ownership & fetch event
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        event = cursor.fetchone()
        if not event:
            raise ValueError("Event not found or access denied")
        event_dict = dict(event)

        # Fetch rescue log entry
        cursor.execute("SELECT * FROM plan_rescue_logs WHERE id = ? AND event_id = ?", (request.rescue_id, event_id))
        rescue_log = cursor.fetchone()
        if not rescue_log:
            raise ValueError("Rescue proposal not found")

        if rescue_log["applied"] == 1:
            raise ValueError("This rescue proposal has already been applied")

        proposal_data = json.loads(rescue_log["full_proposal_json"])
        applied_actions: list[str] = []

        # 1. Apply Event Parameter Updates
        if request.apply_event_updates and proposal_data.get("proposed_event_updates"):
            _apply_event_parameter_updates(
                cursor, event_id, user_id, event_dict, proposal_data["proposed_event_updates"], applied_actions
            )

        # 2. Apply Budget Adjustments
        if request.apply_budget_adjustments and proposal_data.get("proposed_budget_adjustments"):
            _apply_budget_adjustments(cursor, event_id, proposal_data["proposed_budget_adjustments"], applied_actions)

        # 3. Apply Task Actions
        if request.apply_task_actions and proposal_data.get("proposed_task_actions"):
            _apply_task_actions(cursor, event_id, proposal_data["proposed_task_actions"], applied_actions)

        # 4. Mark rescue proposal as applied
        cursor.execute(
            """
            UPDATE plan_rescue_logs
            SET applied = 1, applied_at = CURRENT_TIMESTAMP
            WHERE id = ? AND event_id = ?
            """,
            (request.rescue_id, event_id),
        )

        return {
            "success": True,
            "rescue_id": request.rescue_id,
            "applied_actions": applied_actions,
            "applied_at": datetime.now().isoformat(),
        }
