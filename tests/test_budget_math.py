import pytest
from app.services.budget_service import (
    calculate_budget_summary,
    calculate_budget_scenario_deterministic
)
from app.schemas import BudgetScenarioRequest

def test_distinct_budget_classifications():
    """
    Verifies that Estimates, Quotations, Commitments, and Actual Expenses
    remain strictly distinct and are never conflated.
    """
    items = [
        {
            "category": "Venue",
            "item_name": "Banquet Hall",
            "estimated_amount": 100000.0,
            "quoted_amount": 95000.0,
            "committed_amount": 90000.0,
            "actual_amount": 45000.0, # advance paid
            "status": "committed"
        },
        {
            "category": "Catering",
            "item_name": "Dinner Buffet",
            "estimated_amount": 120000.0,
            "quoted_amount": 130000.0,
            "committed_amount": 0.0, # quoted only, not committed!
            "actual_amount": 0.0,
            "status": "quoted"
        },
        {
            "category": "Photography",
            "item_name": "Traditional + Candid",
            "estimated_amount": 50000.0,
            "quoted_amount": 0.0,
            "committed_amount": 0.0,
            "actual_amount": 0.0,
            "status": "planned"
        }
    ]
    
    planned_budget = 300000.0
    summary = calculate_budget_summary(planned_budget, "INR", items)
    
    # 1. Check totals
    assert summary.planned_budget == 300000.0
    assert summary.total_estimated == 270000.0
    assert summary.total_quoted == 225000.0
    assert summary.total_committed == 90000.0
    assert summary.total_actual == 45000.0
    
    # 2. Check remaining calculations
    assert summary.remaining_from_committed == 210000.0 # 300,000 - 90,000
    assert summary.remaining_from_actual == 255000.0 # 300,000 - 45,000
    
    # 3. Not over budget
    assert summary.is_over_budget is False
    assert summary.over_budget_amount == 0.0
    
    # 4. Check category breakdown
    venue_cat = next(c for c in summary.categories if c.category == "Venue")
    assert venue_cat.estimated_subtotal == 100000.0
    assert venue_cat.quoted_subtotal == 95000.0
    assert venue_cat.committed_subtotal == 90000.0
    assert venue_cat.actual_subtotal == 45000.0

def test_over_budget_detection():
    """Verifies that commitments or actuals exceeding planned budget trigger alerts."""
    items = [
        {
            "category": "Venue",
            "item_name": "Luxury Resort",
            "estimated_amount": 200000.0,
            "quoted_amount": 220000.0,
            "committed_amount": 220000.0,
            "actual_amount": 150000.0
        }
    ]
    planned_budget = 200000.0
    summary = calculate_budget_summary(planned_budget, "INR", items)
    
    assert summary.is_over_budget is True
    assert summary.over_budget_amount == 20000.0
    assert any("Budget exceeded" in alert for alert in summary.alerts)

def test_deterministic_scenario_arithmetic():
    """
    Verifies that budget scenario testing performs strictly deterministic arithmetic,
    handling budget cuts, guest count surges, and additional expenses correctly.
    """
    current_budget = 500000.0
    current_guest_count = 100
    total_committed = 200000.0
    
    # Scenario: 20% budget reduction, +20 guests, +25,000 extra expense
    scenario = BudgetScenarioRequest(
        budget_delta_percent=-20.0, # Budget becomes 400,000
        guest_count_delta=20,       # Guests become 120
        additional_expense=25000.0
    )
    
    res = calculate_budget_scenario_deterministic(
        current_budget=current_budget,
        current_guest_count=current_guest_count,
        total_committed=total_committed,
        scenario=scenario,
        currency="INR"
    )
    
    assert res["original_budget"] == 500000.0
    assert res["projected_budget"] == 400000.0
    assert res["original_guest_count"] == 100
    assert res["projected_guest_count"] == 120
    # Variable cost per guest = (500000 * 0.5) / 100 = 2500
    # 20 extra guests * 2500 = 50,000
    # 50,000 + 25,000 additional = 75,000 cost impact
    assert res["projected_cost_impact"] == 75000.0
    # Total projected expenditure = 200,000 committed + 75,000 = 275,000
    # Projected variance = 400,000 - 275,000 = +125,000
    assert res["projected_variance"] == 125000.0
    assert res["is_feasible"] is True
