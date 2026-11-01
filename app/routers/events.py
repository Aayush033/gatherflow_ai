import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_deps import get_current_user_dep
from app.data.demo_showcase_data import (
    get_demo_budget_items,
    get_demo_event_payload,
    get_demo_plan_payload,
    get_demo_rescue_log,
    get_demo_tasks,
    get_demo_vendors,
)
from app.database import get_db
from app.schemas import EventCreate, EventOut, EventPlanOut, EventUpdate
from app.services import ai_service
from app.vector_db import index_user_vendor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["Events & Planning"])


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, current_user: dict = Depends(get_current_user_dep)) -> EventOut:
    """
    Creates a new event, saves it to persistent storage,
    and initiates initial plan generation.
    """
    event_id = f"evt_{uuid.uuid4().hex[:10]}"
    user_id = current_user["id"]

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
        INSERT INTO events (
            id, user_id, title, event_type, date, time_details, location,
            venue_preferences, guest_count, budget, currency, theme,
            cultural_preferences, dietary_accessibility, priorities_constraints
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                event_id,
                user_id,
                event_in.title,
                event_in.event_type,
                event_in.date,
                event_in.time_details,
                event_in.location,
                event_in.venue_preferences,
                event_in.guest_count,
                event_in.budget,
                event_in.currency,
                event_in.theme,
                event_in.cultural_preferences,
                event_in.dietary_accessibility,
                event_in.priorities_constraints,
            ),
        )

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        created_event = dict(cursor.fetchone())

    # Generate initial plan via Gemini (Workflow A & B & C)
    plan_status = "ready"
    plan_warning = None
    try:
        plan_data = ai_service.generate_initial_event_plan(created_event)
        save_plan_and_seed_items(event_id, plan_data, created_event)
    except ai_service.AIServiceError as e:
        logger.warning("AI initial plan generation could not complete: %s", e)
        plan_status = "unplanned"
        plan_warning = f"Event saved successfully, but AI plan could not be generated: {e!s}. You can retry generating the plan anytime."
    except Exception as e:
        logger.error("Unexpected error seeding plan: %s", e)
        plan_status = "unplanned"
        plan_warning = (
            "Event saved successfully, but AI plan generation failed. You can retry generating the plan anytime."
        )

    created_event["plan_status"] = plan_status
    created_event["plan_warning"] = plan_warning
    return EventOut(**created_event)


@router.post("/demo-showcase", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def seed_demo_showcase_event(current_user: dict = Depends(get_current_user_dep)) -> EventOut:
    """
    Creates or resets a complete demonstration event for evaluators and judges.
    Populates an isolated 250-guest corporate gala with blueprint, budget tiers,
    milestone tasks, linked vendor records, and pre-staged plan rescue log.
    """
    user_id = current_user["id"]
    event_id = f"evt_demo_{user_id[:8]}"
    today = datetime.now().date()
    event_date = (today + timedelta(days=45)).isoformat()

    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Clear any prior demo records for this user to ensure idempotency
        cursor.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        cursor.execute("DELETE FROM event_plans WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM budget_items WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM tasks WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM vendors WHERE event_id = ?", (event_id,))
        cursor.execute("DELETE FROM plan_rescue_logs WHERE event_id = ?", (event_id,))

        # 2. Insert Showcase Event
        cursor.execute(
            """
            INSERT INTO events (
                id, user_id, title, event_type, date, time_details, location,
                venue_preferences, guest_count, budget, currency, theme,
                cultural_preferences, dietary_accessibility, priorities_constraints
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            get_demo_event_payload(event_id, user_id, event_date),
        )

        # 3. Insert Blueprint Plan (honestly marked as pre-staged template)
        cursor.execute(
            """
            INSERT OR REPLACE INTO event_plans (
                id, event_id, concept, theme_details, budget_allocation_json,
                timeline_milestones_json, checklist_json, vendor_categories_json,
                risks_json, contingencies_json, next_actions_json, is_ai_generated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            get_demo_plan_payload(f"plan_demo_{user_id[:8]}", event_id),
        )

        # 4. Insert 4-Tier Budget Items
        budget_rows, b_av_id, b_cater_id = get_demo_budget_items(event_id, user_id)
        for row in budget_rows:
            cursor.execute(
                """
                INSERT OR REPLACE INTO budget_items (id, event_id, category, item_name, estimated_amount, quoted_amount, committed_amount, actual_amount, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )

        # 5. Insert Milestone Tasks
        for task_row in get_demo_tasks(event_id, user_id, today):
            cursor.execute(
                """
                INSERT OR REPLACE INTO tasks (id, event_id, title, category, due_date, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                task_row,
            )

        # 6. Insert User Vendors linked to budget lines
        vendor_rows, vector_vendors = get_demo_vendors(event_id, user_id, b_av_id, b_cater_id)
        for v_row in vendor_rows:
            cursor.execute(
                """
                INSERT OR REPLACE INTO vendors (id, event_id, name, category, contact_person, contact_phone, contact_email, quotation_amount, status, notes, linked_budget_item_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                v_row,
            )

        # 7. Pre-stage Plan Rescue Incident Proposal
        rescue_id = f"rsc_demo_{user_id[:8]}"
        cursor.execute(
            """
            INSERT INTO plan_rescue_logs (id, event_id, scenario_description, proposal_summary, full_proposal_json, applied)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            get_demo_rescue_log(rescue_id, event_id, today),
        )

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        created = dict(cursor.fetchone())

    # Index the vendors into ChromaDB
    try:
        for v_item in vector_vendors:
            index_user_vendor(v_item, event_id=event_id, user_id=user_id)
    except Exception as e:
        logger.warning("Could not index demo vendors into ChromaDB: %s", e)

    created["plan_status"] = "ready"
    created["plan_warning"] = None
    return EventOut(**created)


@router.post("/{event_id}/plan/generate", response_model=EventPlanOut)
def generate_or_retry_event_plan(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> EventPlanOut:
    """
    Dedicated retry action for generating the AI event blueprint and seeded budget/tasks
    if initial planning was unconfigured or failed.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        event_row = cursor.fetchone()
        if not event_row:
            raise HTTPException(status_code=404, detail="Event not found")
        event_dict = dict(event_row)

    try:
        plan_data = ai_service.generate_initial_event_plan(event_dict)
        save_plan_and_seed_items(event_id, plan_data, event_dict)
    except ai_service.AIServiceError as e:
        raise HTTPException(status_code=502, detail=f"AI plan generation failed: {e!s}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan generation error: {e!s}")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM event_plans WHERE event_id = ?", (event_id,))
        saved = cursor.fetchone()
        if not saved:
            raise HTTPException(status_code=404, detail="Generated plan could not be retrieved")
        return EventPlanOut(**dict(saved))


def save_plan_and_seed_items(event_id: str, plan_data: Any, event_dict: dict[str, Any]) -> None:
    """Saves the generated plan and seeds initial budget lines and tasks."""
    plan_id = f"plan_{uuid.uuid4().hex[:10]}"
    event_date_str = event_dict.get("date")
    try:
        event_date = datetime.strptime(event_date_str[:10], "%Y-%m-%d").date()
    except Exception:
        event_date = datetime.now().date() + timedelta(days=60)

    with get_db() as conn:
        cursor = conn.cursor()

        # Save event plan
        cursor.execute(
            """
        INSERT INTO event_plans (
            id, event_id, concept, theme_details, budget_allocation_json,
            timeline_milestones_json, checklist_json, vendor_categories_json,
            risks_json, contingencies_json, next_actions_json, is_ai_generated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ON CONFLICT(event_id) DO UPDATE SET
            concept = excluded.concept,
            theme_details = excluded.theme_details,
            budget_allocation_json = excluded.budget_allocation_json,
            timeline_milestones_json = excluded.timeline_milestones_json,
            checklist_json = excluded.checklist_json,
            vendor_categories_json = excluded.vendor_categories_json,
            risks_json = excluded.risks_json,
            contingencies_json = excluded.contingencies_json,
            next_actions_json = excluded.next_actions_json,
            updated_at = CURRENT_TIMESTAMP
        """,
            (
                plan_id,
                event_id,
                plan_data.concept,
                plan_data.theme_details,
                json.dumps([a.model_dump() for a in plan_data.budget_allocations]),
                json.dumps([m.model_dump() for m in plan_data.timeline_milestones]),
                json.dumps([c.model_dump() for c in plan_data.suggested_checklist]),
                json.dumps(plan_data.vendor_categories),
                json.dumps(plan_data.risks),
                json.dumps(plan_data.contingencies),
                json.dumps(plan_data.next_actions),
            ),
        )

        # Seed initial budget lines if none exist yet (Workflow B)
        cursor.execute("SELECT COUNT(*) as count FROM budget_items WHERE event_id = ?", (event_id,))
        if cursor.fetchone()["count"] == 0:
            for alloc in plan_data.budget_allocations:
                b_id = f"bgt_{uuid.uuid4().hex[:8]}"
                cursor.execute(
                    """
                INSERT INTO budget_items (id, event_id, category, item_name, estimated_amount, status, notes)
                VALUES (?, ?, ?, ?, ?, 'planned', ?)
                """,
                    (
                        b_id,
                        event_id,
                        alloc.category,
                        f"{alloc.category} Package",
                        alloc.estimated_amount,
                        alloc.description or f"Allocated {alloc.percentage}% of planned budget",
                    ),
                )

        # Seed initial checklist tasks if none exist yet (Workflow C)
        cursor.execute("SELECT COUNT(*) as count FROM tasks WHERE event_id = ?", (event_id,))
        if cursor.fetchone()["count"] == 0:
            for item in plan_data.suggested_checklist:
                t_id = f"task_{uuid.uuid4().hex[:8]}"
                days_before = item.suggested_days_before or 14
                task_due = (event_date - timedelta(days=days_before)).isoformat()
                cursor.execute(
                    """
                INSERT INTO tasks (id, event_id, title, category, due_date, priority, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, 'todo', ?)
                """,
                    (
                        t_id,
                        event_id,
                        item.task,
                        item.category,
                        task_due,
                        item.priority,
                        f"Suggested deadline {days_before} days prior to event",
                    ),
                )


@router.get("", response_model=list[EventOut])
def list_events(current_user: dict = Depends(get_current_user_dep)) -> list[EventOut]:
    """Returns only events owned by the authenticated user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE user_id = ? ORDER BY created_at DESC", (current_user["id"],))
        return [EventOut(**dict(row)) for row in cursor.fetchall()]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> EventOut:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventOut(**dict(row))


@router.patch("/{event_id}", response_model=EventOut)
def update_event(
    event_id: str, event_update: EventUpdate, current_user: dict = Depends(get_current_user_dep)
) -> EventOut:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")

        update_data = event_update.model_dump(exclude_unset=True)
        if not update_data:
            return EventOut(**dict(row))

        clauses = [f"{k} = ?" for k in update_data.keys()]
        clauses.append("updated_at = CURRENT_TIMESTAMP")
        values = list(update_data.values())
        values.extend([event_id, current_user["id"]])

        cursor.execute(f"UPDATE events SET {', '.join(clauses)} WHERE id = ? AND user_id = ?", values)

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        return EventOut(**dict(cursor.fetchone()))


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> None:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Event not found")


@router.get("/{event_id}/plan", response_model=EventPlanOut | None)
def get_event_plan(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> EventPlanOut | None:
    with get_db() as conn:
        cursor = conn.cursor()
        # Verify ownership
        cursor.execute("SELECT id FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Event not found")

        cursor.execute("SELECT * FROM event_plans WHERE event_id = ?", (event_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return EventPlanOut(**dict(row))


@router.post("/{event_id}/plan/generate", response_model=EventPlanOut)
def regenerate_event_plan(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> EventPlanOut:
    """Explicitly triggers Gemini to generate or refresh the event plan."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        event_row = cursor.fetchone()
        if not event_row:
            raise HTTPException(status_code=404, detail="Event not found")
        event_dict = dict(event_row)

    try:
        plan_data = ai_service.generate_initial_event_plan(event_dict)
        save_plan_and_seed_items(event_id, plan_data, event_dict)
    except ai_service.AIServiceError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate plan: {e!s}")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM event_plans WHERE event_id = ?", (event_id,))
        return EventPlanOut(**dict(cursor.fetchone()))
