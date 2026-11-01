import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth_deps import get_current_user_dep
from app.database import get_db
from app.schemas import EventCreate, EventOut, EventPlanOut, EventUpdate
from app.services import ai_service
from app.vector_db import index_user_vendor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["Events & Planning"])


@router.post("", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, current_user: dict = Depends(get_current_user_dep)):
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
        logger.warning(f"AI initial plan generation could not complete: {e}")
        plan_status = "unplanned"
        plan_warning = f"Event saved successfully, but AI plan could not be generated: {e!s}. You can retry generating the plan anytime."
    except Exception as e:
        logger.error(f"Unexpected error seeding plan: {e}")
        plan_status = "unplanned"
        plan_warning = (
            "Event saved successfully, but AI plan generation failed. You can retry generating the plan anytime."
        )

    created_event["plan_status"] = plan_status
    created_event["plan_warning"] = plan_warning
    return EventOut(**created_event)


@router.post("/demo-showcase", response_model=EventOut, status_code=status.HTTP_201_CREATED)
def seed_demo_showcase_event(current_user: dict = Depends(get_current_user_dep)):
    """
    Creates or resets a complete, rich demonstration event for evaluators and judges.
    Instantly populates a realistic 250-guest corporate gala with:
    - AI Event Blueprint & 4 Milestones
    - 4-Tier Budget Items ($50k budget, paid, committed, quoted, planned items)
    - Milestone Checklist Tasks across priorities
    - Linked Vendors indexed in ChromaDB
    - Pre-staged Plan Rescue Incident
    Enables judges to test the entire application in under 2 seconds.
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
            (
                event_id,
                user_id,
                "🌟 Global Tech & Innovation Gala 2026",
                "corporate",
                event_date,
                "18:00 - 23:30 (Keynote at 19:15, Banquet Dinner at 20:30)",
                "Metropolitan Convention Center — Grand Ballroom, Hall A",
                "Full A/V setup, motorized projection walls, dual catering prep kitchens",
                250,
                50000.0,
                "USD",
                "Modern Cyber Elegance & Luminescent Architecture",
                "International business formal, multilingual greeting materials",
                "35 Vegan/GF pre-registered; ADA compliant ramps to all stages",
                "Zero audiovisual latency, strict $50,000 budget cap, executive VIP lounge",
            ),
        )

        # 3. Insert Blueprint Plan
        budget_allocations = [
            {
                "category": "Venue",
                "percentage": 30.0,
                "estimated_amount": 15000.0,
                "description": "Grand ballroom & VIP green room rental",
            },
            {
                "category": "Catering",
                "percentage": 36.0,
                "estimated_amount": 18000.0,
                "description": "Executive 4-course dinner & open bar package",
            },
            {
                "category": "Audiovisual",
                "percentage": 17.0,
                "estimated_amount": 8500.0,
                "description": "Concert-grade sound & dual 4K LED walls",
            },
            {
                "category": "Entertainment",
                "percentage": 9.0,
                "estimated_amount": 4500.0,
                "description": "Keynote speaker honorarium & travel",
            },
            {
                "category": "Decor",
                "percentage": 8.0,
                "estimated_amount": 4000.0,
                "description": "Luminescent centerpieces & ambient uplighting",
            },
        ]
        milestones = [
            {
                "milestone": "Contracts & Venue Deposit Finalized",
                "target_days_before": 45,
                "description": "Lock space and liability insurance",
            },
            {
                "milestone": "Vendor Technical Rehearsal Lock",
                "target_days_before": 14,
                "description": "Final sound checks and culinary tastings",
            },
            {
                "milestone": "VIP Invitation Roster Confirmation",
                "target_days_before": 7,
                "description": "Seat assignments and dietary badges",
            },
            {
                "milestone": "Gala Day Execution & Live Stage Runs",
                "target_days_before": 0,
                "description": "On-site command center operations",
            },
        ]
        checklist = [
            {
                "task": "Execute Grand Ballroom Lease & Liability Insurance",
                "category": "Venue",
                "suggested_days_before": 35,
                "priority": "high",
            },
            {
                "task": "Approve Audio/Visual Rider & LED Wall Schematics",
                "category": "Audiovisual",
                "suggested_days_before": 20,
                "priority": "high",
            },
            {
                "task": "Complete VIP Catering Menu Tasting & Dietary List",
                "category": "Catering",
                "suggested_days_before": 18,
                "priority": "high",
            },
            {
                "task": "Send QR-Code Entry Passes to 250 Registered Guests",
                "category": "Logistics",
                "suggested_days_before": 10,
                "priority": "medium",
            },
            {
                "task": "Full Production Stage Rehearsal & Lighting Cues",
                "category": "Production",
                "suggested_days_before": 1,
                "priority": "high",
            },
            {
                "task": "Post-Gala Financial Reconciliation & Deposit Return",
                "category": "Finance",
                "suggested_days_before": -3,
                "priority": "low",
            },
        ]
        cursor.execute(
            """
        INSERT OR REPLACE INTO event_plans (
            id, event_id, concept, theme_details, budget_allocation_json,
            timeline_milestones_json, checklist_json, vendor_categories_json,
            risks_json, contingencies_json, next_actions_json, is_ai_generated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """,
            (
                f"plan_demo_{user_id[:8]}",
                event_id,
                "A flagship corporate celebration blending executive networking, keynote thought leadership, and cinematic audiovisual immersion. Structured into three strategic phases: Welcome Cocktail Reception, Keynote & Awards, and Interactive Networking Gala.",
                "Deep obsidian and navy base accented by warm amber uplighting and frosted glass installations. Sustainable digital signage and branded interactive touchpoints throughout.",
                json.dumps(budget_allocations),
                json.dumps(milestones),
                json.dumps(checklist),
                json.dumps(["Venue", "Catering", "Audiovisual", "Entertainment", "Decor"]),
                json.dumps(
                    [
                        "High demand for A/V engineers during conference week",
                        "Severe weather causing airport transit delays for VIP speakers",
                        "Dietary overflow requiring on-demand kitchen adjustments",
                    ]
                ),
                json.dumps(
                    [
                        "Secondary A/V production team on 2-hour standby retainer",
                        "Pre-arranged 10% banquet buffer with catering director",
                        "Dual remote fiber link for live virtual keynote fallback",
                    ]
                ),
                json.dumps(
                    [
                        {
                            "action": "Review signed technical rider with Apex AV Productions",
                            "priority": "high",
                            "timeline": "This week",
                        },
                        {
                            "action": "Conduct final dietary count verification",
                            "priority": "medium",
                            "timeline": "Next week",
                        },
                    ]
                ),
            ),
        )

        # 4. Insert 4-Tier Budget Items
        b_venue = f"bgt_demo_venue_{user_id[:6]}"
        b_cater = f"bgt_demo_cater_{user_id[:6]}"
        b_av = f"bgt_demo_av_{user_id[:6]}"
        b_keynote = f"bgt_demo_key_{user_id[:6]}"
        b_decor = f"bgt_demo_dec_{user_id[:6]}"

        budget_rows = [
            (
                b_venue,
                event_id,
                "Venue",
                "Grand Ballroom & VIP Suite",
                15000.0,
                15000.0,
                15000.0,
                15000.0,
                "paid",
                "Fully settled. Security deposit refundable.",
            ),
            (
                b_cater,
                event_id,
                "Catering",
                "Executive 4-Course Banquet & Bar",
                18000.0,
                17500.0,
                0.0,
                0.0,
                "quoted",
                "Quote from Savor Gourmet Catering for 250 guests.",
            ),
            (
                b_av,
                event_id,
                "Audiovisual",
                "Concert Sound, Dual 4K LED Walls & Truss",
                8500.0,
                7800.0,
                7800.0,
                0.0,
                "committed",
                "Contract executed with Apex AV Productions.",
            ),
            (
                b_keynote,
                event_id,
                "Entertainment",
                "Keynote Speaker Honorarium & VIP Travel",
                4500.0,
                0.0,
                0.0,
                0.0,
                "planned",
                "Targeting industry pioneer; legal contract draft under review.",
            ),
            (
                b_decor,
                event_id,
                "Decor",
                "Luminescent Uplighting & Table Centerpieces",
                4000.0,
                3800.0,
                0.0,
                0.0,
                "quoted",
                "Includes setup and strike by 01:00.",
            ),
        ]
        for row in budget_rows:
            cursor.execute(
                """
            INSERT OR REPLACE INTO budget_items (id, event_id, category, item_name, estimated_amount, quoted_amount, committed_amount, actual_amount, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                row,
            )

        # 5. Insert Milestone Tasks
        tasks_data = [
            (
                f"tsk_demo_1_{user_id[:6]}",
                event_id,
                "Secure Grand Ballroom Lease & Liability Insurance",
                "Venue",
                (today + timedelta(days=10)).isoformat(),
                "high",
                "completed",
                "Executed and paid in full.",
            ),
            (
                f"tsk_demo_2_{user_id[:6]}",
                event_id,
                "Approve Audio/Visual Rider & LED Wall Schematics",
                "Audiovisual",
                (today + timedelta(days=25)).isoformat(),
                "high",
                "in_progress",
                "Marcus Vance coordinating crew schedule.",
            ),
            (
                f"tsk_demo_3_{user_id[:6]}",
                event_id,
                "Complete VIP Catering Menu Tasting & Dietary List",
                "Catering",
                (today + timedelta(days=27)).isoformat(),
                "high",
                "in_progress",
                "Chef Elena confirmed 35 vegan/GF courses.",
            ),
            (
                f"tsk_demo_4_{user_id[:6]}",
                event_id,
                "Send QR-Code Entry Passes to 250 Registered Guests",
                "Logistics",
                (today + timedelta(days=35)).isoformat(),
                "medium",
                "completed",
                "Automated digital invitations sent.",
            ),
            (
                f"tsk_demo_5_{user_id[:6]}",
                event_id,
                "Full Production Stage Rehearsal & Lighting Cues",
                "Production",
                (today + timedelta(days=44)).isoformat(),
                "high",
                "todo",
                "Scheduled for 16:00 day before event.",
            ),
            (
                f"tsk_demo_6_{user_id[:6]}",
                event_id,
                "Post-Gala Financial Reconciliation & Deposit Return",
                "Finance",
                (today + timedelta(days=48)).isoformat(),
                "low",
                "todo",
                "Review final supplier invoices against commitments.",
            ),
        ]
        for t in tasks_data:
            cursor.execute(
                """
            INSERT OR REPLACE INTO tasks (id, event_id, title, category, due_date, priority, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                t,
            )

        # 6. Insert User Vendors linked to budget lines
        v_av_id = f"vnd_demo_av_{user_id[:6]}"
        v_cater_id = f"vnd_demo_cat_{user_id[:6]}"
        vendors_data = [
            (
                v_av_id,
                event_id,
                "Apex Audiovisuals & Production",
                "Audiovisual",
                "Marcus Vance",
                "+1 (555) 234-5678",
                "marcus@apexav.example.com",
                7800.0,
                "confirmed",
                "Verified supplier. Includes 3 dedicated on-site sound engineers.",
                b_av,
            ),
            (
                v_cater_id,
                event_id,
                "Savor Gourmet Catering & Events",
                "Catering",
                "Elena Rostova",
                "+1 (555) 876-5432",
                "elena@savorcater.example.com",
                17500.0,
                "quoted",
                "Full plated service + bar package for 250 attendees.",
                b_cater,
            ),
        ]
        for v in vendors_data:
            cursor.execute(
                """
            INSERT OR REPLACE INTO vendors (id, event_id, name, category, contact_person, contact_phone, contact_email, quotation_amount, status, notes, linked_budget_item_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                v,
            )

        # 7. Pre-stage a Plan Rescue Incident Proposal
        rescue_id = f"rsc_demo_{user_id[:8]}"
        rescue_proposal = {
            "incident": "Lead Keynote Speaker canceled due to international flight disruption 4 days before gala.",
            "impact_assessment": "High programmatic visibility impact. No immediate financial penalty as speaker agreement included force majeure flight disruption clause.",
            "recommended_strategy": "Activate verified local keynote speaker on pre-cleared backup list; shift $1,000 speaker budget savings toward expedited presentation rehearsal.",
            "budget_adjustments": [
                {
                    "category": "Entertainment",
                    "item_name": "Keynote Speaker (Local Alternative)",
                    "amount_change": -1000.0,
                    "rationale": "Local speaker honorarium is $3,500 vs $4,500 allocated (saves $1,000)",
                },
                {
                    "category": "Audiovisual",
                    "item_name": "Expedited Slide Rehearsal Support",
                    "amount_change": 300.0,
                    "rationale": "Extra 1-hr technician setup for slide reformatting",
                },
            ],
            "timeline_adjustments": [
                {
                    "task": "Conduct Emergency Keynote Virtual Onboarding & Audio Check",
                    "due_date": (today + timedelta(days=42)).isoformat(),
                    "action": "add",
                }
            ],
            "guest_impact": "Zero disruption to gala schedule; attendees receive full keynote programming as planned.",
        }
        cursor.execute(
            """
        INSERT INTO plan_rescue_logs (id, event_id, scenario_description, proposal_summary, full_proposal_json, applied)
        VALUES (?, ?, ?, ?, ?, 0)
        """,
            (
                rescue_id,
                event_id,
                "Lead Keynote Speaker canceled due to international flight disruption 4 days before gala.",
                "Activate verified local keynote speaker on pre-cleared backup list; saves $1,000.",
                json.dumps(rescue_proposal),
            ),
        )

        cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
        created = dict(cursor.fetchone())

    # Index the vendors into ChromaDB
    try:
        index_user_vendor(
            {
                "id": v_av_id,
                "name": "Apex Audiovisuals & Production",
                "category": "Audiovisual",
                "quotation_amount": 7800.0,
                "notes": "Verified supplier. Includes 3 dedicated on-site sound engineers.",
            },
            event_id=event_id,
            user_id=user_id,
        )
        index_user_vendor(
            {
                "id": v_cater_id,
                "name": "Savor Gourmet Catering & Events",
                "category": "Catering",
                "quotation_amount": 17500.0,
                "notes": "Full plated service + bar package for 250 attendees.",
            },
            event_id=event_id,
            user_id=user_id,
        )
    except Exception as e:
        logger.warning(f"Could not index demo vendors into ChromaDB: {e}")

    created["plan_status"] = "ready"
    created["plan_warning"] = None
    return EventOut(**created)


@router.post("/{event_id}/plan/generate", response_model=EventPlanOut)
def generate_or_retry_event_plan(event_id: str, current_user: dict = Depends(get_current_user_dep)):
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
def list_events(current_user: dict = Depends(get_current_user_dep)):
    """Returns only events owned by the authenticated user."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE user_id = ? ORDER BY created_at DESC", (current_user["id"],))
        return [EventOut(**dict(row)) for row in cursor.fetchall()]


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, current_user: dict = Depends(get_current_user_dep)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Event not found")
        return EventOut(**dict(row))


@router.patch("/{event_id}", response_model=EventOut)
def update_event(event_id: str, event_update: EventUpdate, current_user: dict = Depends(get_current_user_dep)):
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
def delete_event(event_id: str, current_user: dict = Depends(get_current_user_dep)):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, current_user["id"]))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Event not found")


@router.get("/{event_id}/plan", response_model=EventPlanOut | None)
def get_event_plan(event_id: str, current_user: dict = Depends(get_current_user_dep)):
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
def regenerate_event_plan(event_id: str, current_user: dict = Depends(get_current_user_dep)):
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
