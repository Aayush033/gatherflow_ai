from datetime import date
from typing import Any

from fastapi import APIRouter, Depends

from app.auth_deps import get_current_user_dep, verify_event_ownership
from app.database import get_db
from app.schemas import (
    BlueprintHealthIndicators,
    BudgetSummaryOut,
    EventBlueprintOut,
    EventOut,
    EventPlanOut,
    NextBestAction,
    TaskSummaryOut,
)
from app.services.budget_service import calculate_budget_summary
from app.services.task_service import compute_task_summary, evaluate_task, parse_date

router = APIRouter(prefix="/api/events/{event_id}/blueprint", tags=["Event Blueprint"])


def calculate_plan_health(
    event: dict[str, Any],
    budget_summary: BudgetSummaryOut,
    task_summary: TaskSummaryOut,
    vendors: list[dict[str, Any]],
    days_to_event: int,
) -> BlueprintHealthIndicators:
    """
    Objectively computes plan health strictly from stored records.
    Never invents statistics or fabricates progress percentages.
    """
    alerts = []
    score = 100

    # 1. Overdue task assessment
    has_overdue = task_summary.overdue_tasks > 0
    if has_overdue:
        score -= min(35, task_summary.overdue_tasks * 10)
        alerts.append(f"{task_summary.overdue_tasks} task(s) currently overdue.")

    # 2. Budget critical assessment
    is_budget_critical = budget_summary.is_over_budget
    budget_usage_percent = 0.0
    if budget_summary.planned_budget > 0:
        budget_usage_percent = round((budget_summary.total_committed / budget_summary.planned_budget) * 100.0, 1)

    if is_budget_critical:
        score -= 30
        alerts.append(
            f"Committed budget exceeds plan by {budget_summary.currency} {budget_summary.over_budget_amount:,.2f}."
        )
    elif budget_usage_percent > 90.0:
        score -= 10
        alerts.append(f"Committed budget is at {budget_usage_percent}% of total allocation.")

    # 3. Unconfirmed critical vendors
    # Check if critical categories (Venue, Catering) have confirmed vendors
    critical_categories = {"venue", "catering"}
    confirmed_categories = {
        vendor.get("category", "").lower() for vendor in vendors if vendor.get("status") == "confirmed"
    }
    missing_critical = [
        category_name.capitalize() for category_name in critical_categories if category_name not in confirmed_categories
    ]
    unconfirmed_critical_count = len(missing_critical)

    if unconfirmed_critical_count > 0 and days_to_event <= 30:
        score -= unconfirmed_critical_count * 15
        alerts.append(
            f"Critical vendor(s) not yet confirmed: {', '.join(missing_critical)} with {days_to_event} days remaining."
        )

    # 4. Time crunch penalty
    if days_to_event < 7 and task_summary.progress_percentage < 70.0:
        score -= 20
        alerts.append(f"Event is within 7 days, but only {task_summary.progress_percentage}% of tasks are completed.")

    score = max(5, min(100, score))

    if score >= 80:
        health_status = "On Track"
    elif score >= 50:
        health_status = "Needs Attention"
    else:
        health_status = "Critical Action Required"

    return BlueprintHealthIndicators(
        has_overdue_tasks=has_overdue,
        overdue_task_count=task_summary.overdue_tasks,
        is_budget_critical=is_budget_critical,
        budget_usage_percent=budget_usage_percent,
        unconfirmed_critical_vendors=unconfirmed_critical_count,
        days_to_event=days_to_event,
        health_score=score,
        health_status=health_status,
        alert_messages=alerts,
    )


def determine_next_best_action(
    event: dict[str, Any],
    budget_summary: BudgetSummaryOut,
    task_summary: TaskSummaryOut,
    tasks: list[dict[str, Any]],
    vendors: list[dict[str, Any]],
    health: BlueprintHealthIndicators,
) -> NextBestAction:
    """
    Determines the single most contextually urgent Next Best Action
    using deterministic business priorities.
    """
    # 1. Budget overrun takes emergency priority
    if health.is_budget_critical:
        return NextBestAction(
            title="Launch Plan Rescue to Absorb Budget Overrun",
            description=f"Your commitments exceed your budget by {budget_summary.currency} {budget_summary.over_budget_amount:,.2f}. Use Plan Rescue AI to adapt category allocations and restore financial balance.",
            action_type="plan_rescue",
            urgency="critical",
            action_url="#rescue",
        )

    # 2. Overdue high-priority tasks
    overdue_tasks = [task_item for task_item in tasks if task_item.get("is_overdue")]
    if overdue_tasks:
        high_overdue = next(
            (task_item for task_item in overdue_tasks if task_item.get("priority") in ("high", "critical")),
            overdue_tasks[0],
        )
        return NextBestAction(
            title=f"Resolve Overdue Task: {high_overdue.get('title')}",
            description=f"This task is overdue for the category '{high_overdue.get('category')}'. Update its due date, assign an owner, or mark it completed.",
            action_type="task",
            urgency="high",
            action_url="#timeline",
        )

    # 3. Unconfirmed critical vendors near deadline
    if health.unconfirmed_critical_vendors > 0 and health.days_to_event <= 45:
        return NextBestAction(
            title="Confirm Core Venue & Catering Vendors",
            description=f"With {health.days_to_event} days remaining, confirming your venue and caterer locks in date security and the biggest cost variables.",
            action_type="vendor",
            urgency="high",
            action_url="#vendors",
        )

    # 4. Incomplete budget planning
    if budget_summary.total_estimated == 0 and budget_summary.total_committed == 0:
        return NextBestAction(
            title="Establish Line-Item Budget Estimates",
            description="Your event has no recorded budget line items yet. Review the AI proposed allocations in the Budget Studio to establish realistic targets.",
            action_type="budget",
            urgency="medium",
            action_url="#budget",
        )

    # 5. Next upcoming task
    upcoming_tasks = [t for t in tasks if t.get("status") != "completed" and not t.get("is_overdue")]
    if upcoming_tasks:
        next_task = upcoming_tasks[0]
        days_str = (
            f"due in {next_task.get('days_remaining')} day(s)"
            if next_task.get("days_remaining") is not None
            else "no due date set"
        )
        return NextBestAction(
            title=f"Complete Upcoming Task: {next_task.get('title')}",
            description=f"Next priority milestone in '{next_task.get('category')}' ({days_str}).",
            action_type="task",
            urgency="medium",
            action_url="#timeline",
        )

    # 6. Default healthy state
    return NextBestAction(
        title="Review Vendor Quotations and Contingencies",
        description="All current tasks are on schedule! Compare outstanding vendor quotes or test 'What-If' scenarios to prepare for contingencies.",
        action_type="contingency",
        urgency="low",
        action_url="#vendors",
    )


@router.get("", response_model=EventBlueprintOut)
def get_event_blueprint(event_id: str, current_user: dict = Depends(get_current_user_dep)) -> EventBlueprintOut:
    # Verify ownership & fetch event
    event_dict = verify_event_ownership(event_id, current_user["id"])

    with get_db() as conn:
        cursor = conn.cursor()

        # Fetch plan
        cursor.execute("SELECT * FROM event_plans WHERE event_id = ?", (event_id,))
        plan_row = cursor.fetchone()
        plan_out = EventPlanOut(**dict(plan_row)) if plan_row else None

        # Fetch budget items
        cursor.execute("SELECT * FROM budget_items WHERE event_id = ? ORDER BY created_at ASC", (event_id,))
        budget_items = [dict(r) for r in cursor.fetchall()]
        budget_summary = calculate_budget_summary(event_dict["budget"], event_dict["currency"], budget_items)

        # Fetch tasks
        cursor.execute("SELECT * FROM tasks WHERE event_id = ? ORDER BY due_date ASC", (event_id,))
        task_rows = [dict(r) for r in cursor.fetchall()]
        for t in task_rows:
            is_overdue, days_rem = evaluate_task(t)
            t["is_overdue"] = is_overdue
            t["days_remaining"] = days_rem
        task_summary = compute_task_summary(task_rows)

        # Fetch vendors
        cursor.execute("SELECT * FROM vendors WHERE event_id = ?", (event_id,))
        vendor_rows = [dict(r) for r in cursor.fetchall()]

    # Calculate days to event
    event_date = parse_date(event_dict.get("date"))
    days_to_event = (event_date - date.today()).days if event_date else 0

    # Calculate health indicators and next best action
    health = calculate_plan_health(event_dict, budget_summary, task_summary, vendor_rows, days_to_event)
    next_action = determine_next_best_action(event_dict, budget_summary, task_summary, task_rows, vendor_rows, health)

    return EventBlueprintOut(
        event=EventOut(**event_dict),
        plan=plan_out,
        budget_summary=budget_summary,
        task_summary=task_summary,
        health=health,
        next_best_action=next_action,
    )
