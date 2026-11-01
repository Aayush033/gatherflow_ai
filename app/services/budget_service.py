from typing import Any

from app.schemas import (
    BudgetScenarioRequest,
    BudgetSummaryOut,
    CategoryBudgetBreakdown,
)


def calculate_budget_summary(planned_budget: float, currency: str, items: list[dict[str, Any]]) -> BudgetSummaryOut:
    """
    Deterministically computes budget totals, keeping Estimates, Quotations,
    Commitments, and Actual Expenses strictly distinct.
    """
    total_estimated = 0.0
    total_quoted = 0.0
    total_committed = 0.0
    total_actual = 0.0

    category_map: dict[str, dict[str, Any]] = {}

    for item in items:
        estimated_val = float(item.get("estimated_amount", 0.0) or 0.0)
        quoted_val = float(item.get("quoted_amount", 0.0) or 0.0)
        committed_val = float(item.get("committed_amount", 0.0) or 0.0)
        actual_val = float(item.get("actual_amount", 0.0) or 0.0)
        category_name = str(item.get("category", "General") or "General").strip()

        total_estimated += estimated_val
        total_quoted += quoted_val
        total_committed += committed_val
        total_actual += actual_val

        if category_name not in category_map:
            category_map[category_name] = {
                "category": category_name,
                "estimated_subtotal": 0.0,
                "quoted_subtotal": 0.0,
                "committed_subtotal": 0.0,
                "actual_subtotal": 0.0,
                "item_count": 0,
            }
        category_map[category_name]["estimated_subtotal"] += estimated_val
        category_map[category_name]["quoted_subtotal"] += quoted_val
        category_map[category_name]["committed_subtotal"] += committed_val
        category_map[category_name]["actual_subtotal"] += actual_val
        category_map[category_name]["item_count"] += 1

    # Round all values to 2 decimal places to ensure precision
    total_estimated = round(total_estimated, 2)
    total_quoted = round(total_quoted, 2)
    total_committed = round(total_committed, 2)
    total_actual = round(total_actual, 2)
    planned_budget = round(planned_budget, 2)

    # Remaining budget calculations:
    # 1. Remaining from actual paid: planned - actual
    # 2. Remaining after commitments (the safest metric): planned - committed
    remaining_from_actual = round(planned_budget - total_actual, 2)
    remaining_from_committed = round(planned_budget - total_committed, 2)

    is_over_budget = total_committed > planned_budget or total_actual > planned_budget
    over_budget_amount = round(max(0.0, total_committed - planned_budget, total_actual - planned_budget), 2)

    alerts: list[str] = []
    if is_over_budget:
        alerts.append(f"Budget exceeded by {currency} {over_budget_amount:,.2f} based on commitments.")
    elif total_committed > (planned_budget * 0.9):
        alerts.append(
            f"Caution: 90% of planned budget is already committed ({currency} {total_committed:,.2f} of {currency} {planned_budget:,.2f})."
        )

    if total_estimated > planned_budget:
        alerts.append(
            f"Estimated costs ({currency} {total_estimated:,.2f}) exceed planned budget ({currency} {planned_budget:,.2f}). Scope refinement needed."
        )

    categories = [
        CategoryBudgetBreakdown(
            category=data["category"],
            estimated_subtotal=round(data["estimated_subtotal"], 2),
            quoted_subtotal=round(data["quoted_subtotal"], 2),
            committed_subtotal=round(data["committed_subtotal"], 2),
            actual_subtotal=round(data["actual_subtotal"], 2),
            item_count=data["item_count"],
        )
        for data in category_map.values()
    ]

    # Sort categories by committed subtotal descending
    categories.sort(key=lambda c: c.committed_subtotal, reverse=True)

    return BudgetSummaryOut(
        planned_budget=planned_budget,
        total_estimated=total_estimated,
        total_quoted=total_quoted,
        total_committed=total_committed,
        total_actual=total_actual,
        remaining_from_committed=remaining_from_committed,
        remaining_from_actual=remaining_from_actual,
        currency=currency,
        is_over_budget=is_over_budget,
        over_budget_amount=over_budget_amount,
        alerts=alerts,
        categories=categories,
    )


def calculate_budget_scenario_deterministic(
    current_budget: float,
    current_guest_count: int,
    total_committed: float,
    scenario: BudgetScenarioRequest,
    currency: str = "INR",
) -> dict[str, Any]:
    """
    Computes purely deterministic numerical scenario projections.
    Does NOT hallucinate or delegate arithmetic to an AI model.
    """
    # 1. Budget changes
    budget_multiplier = 1.0 + ((scenario.budget_delta_percent or 0.0) / 100.0)
    projected_budget = round(max(0.0, current_budget * budget_multiplier), 2)

    # 2. Guest changes
    guest_delta = scenario.guest_count_delta or 0
    projected_guest_count = max(1, current_guest_count + guest_delta)

    # Variable cost estimation based on per-guest ratio
    # Typically food, venue capacity, favors scale with guests (assumed 50% variable cost baseline)
    cost_per_guest = (current_budget * 0.5) / max(1, current_guest_count)
    variable_guest_impact = round(guest_delta * cost_per_guest, 2)

    additional_expense = round(scenario.additional_expense or 0.0, 2)

    total_cost_impact = round(variable_guest_impact + additional_expense, 2)

    # Projected spending = committed baseline + impacts
    projected_total_spending = round(total_committed + total_cost_impact, 2)
    projected_variance = round(projected_budget - projected_total_spending, 2)

    is_feasible = projected_variance >= 0

    analysis_lines = [
        f"Original budget: {currency} {current_budget:,.2f} | Projected budget: {currency} {projected_budget:,.2f} ({scenario.budget_delta_percent:+0.1f}%)",
        f"Original guests: {current_guest_count} | Projected guests: {projected_guest_count} ({guest_delta:+d} guests)",
        f"Estimated cost impact from guest change: {currency} {variable_guest_impact:+,.2f} (at approx {currency} {cost_per_guest:,.2f}/guest variable)",
        f"Additional direct expense: {currency} {additional_expense:,.2f}",
        f"Total projected expenditure: {currency} {projected_total_spending:,.2f}",
        f"Projected balance / deficit: {currency} {projected_variance:+,.2f}",
    ]

    if not is_feasible:
        analysis_lines.append(
            f"WARNING: Deficit of {currency} {abs(projected_variance):,.2f}. Vendor concessions or category trimming required."
        )
    else:
        analysis_lines.append(f"Feasible: Projected surplus of {currency} {projected_variance:,.2f} remaining.")

    return {
        "original_budget": current_budget,
        "projected_budget": projected_budget,
        "original_guest_count": current_guest_count,
        "projected_guest_count": projected_guest_count,
        "projected_cost_impact": total_cost_impact,
        "projected_variance": projected_variance,
        "is_feasible": is_feasible,
        "deterministic_analysis": "\n".join(analysis_lines),
    }
