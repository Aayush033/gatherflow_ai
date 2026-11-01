from unittest.mock import patch


def test_plan_rescue_full_connected_workflow(client, test_user_headers):
    """
    Verifies Signature Differentiator (Plan Rescue AI):
    1. Creates an event with budget and tasks.
    2. Simulates an emergency disruption (e.g. 20% budget cut).
    3. Proposes an adaptive replan with trade-offs.
    4. Confirms that records are NOT modified before approval.
    5. User approves and applies changes.
    6. Confirms that persistent database records are accurately updated.
    """
    # 1. Create initial event
    create_payload = {
        "title": "Diwali Community Mela 2026",
        "event_type": "community",
        "date": "2026-11-01",
        "location": "Central Grounds, Pune",
        "guest_count": 500,
        "budget": 200000.0,
        "currency": "INR",
        "theme": "Festival of Lights",
    }
    create_res = client.post("/api/events", json=create_payload, headers=test_user_headers)
    assert create_res.status_code == 201
    event_id = create_res.json()["id"]

    # 2. Add a budget item
    bgt_res = client.post(
        f"/api/events/{event_id}/budget/items",
        json={"category": "Lighting", "item_name": "Fairy Lights & Lamps", "estimated_amount": 50000.0},
        headers=test_user_headers,
    )
    assert bgt_res.status_code == 201

    # 3. Mock Gemini call during rescue proposal generation
    mock_ai_output = {
        "situation_summary": "Absorb sudden 20% budget cut while preserving festival atmosphere.",
        "tradeoffs_and_impact": "Downscale decorative lighting structures and switch to community volunteers.",
        "ai_assumptions": ["Local volunteers available for setup", "Stage sound system is already subsidized"],
        "proposed_event_updates": {"budget": 160000.0, "guest_count": None, "date": None},
        "proposed_budget_adjustments": [
            {
                "category": "Lighting",
                "item_name": "Fairy Lights & Lamps",
                "current_estimate": 50000.0,
                "proposed_estimate": 35000.0,
                "adjustment_reason": "Scale down perimeter lighting grid",
            }
        ],
        "proposed_task_actions": [
            {
                "action": "add",
                "title": "Recruit volunteer lighting coordinators",
                "category": "Volunteers",
                "priority": "high",
                "due_date": "2026-10-25",
                "notes": "Plan Rescue: volunteer coordination",
            }
        ],
        "immediate_actions": ["Confirm volunteer captain", "Notify lighting contractor"],
    }

    with patch("app.services.rescue_service.generate_plan_rescue_proposal", return_value=mock_ai_output):
        rescue_req = {
            "scenario_type": "budget_cut",
            "description": "Sponsor backed out; need to cut 40,000 INR immediately",
            "target_budget": 160000.0,
        }
        prop_res = client.post(f"/api/events/{event_id}/rescue/propose", json=rescue_req, headers=test_user_headers)
        assert prop_res.status_code == 200
        proposal = prop_res.json()
        rescue_id = proposal["rescue_id"]
        assert proposal["situation_summary"] == mock_ai_output["situation_summary"]
        assert len(proposal["confirmed_facts"]) > 0

    # 4. Verify that records have NOT changed yet (Strict Release Gate!)
    ev_check = client.get(f"/api/events/{event_id}", headers=test_user_headers).json()
    assert ev_check["budget"] == 200000.0  # Still 200,000!

    # 5. User explicitly reviews and applies proposal
    apply_payload = {
        "rescue_id": rescue_id,
        "apply_event_updates": True,
        "apply_budget_adjustments": True,
        "apply_task_actions": True,
    }
    apply_res = client.post(f"/api/events/{event_id}/rescue/apply", json=apply_payload, headers=test_user_headers)
    assert apply_res.status_code == 200
    apply_result = apply_res.json()
    assert apply_result["success"] is True

    # 6. Verify that event budget is now 160,000
    ev_updated = client.get(f"/api/events/{event_id}", headers=test_user_headers).json()
    assert ev_updated["budget"] == 160000.0

    # 7. Verify that budget item was adjusted
    bgt_items = client.get(f"/api/events/{event_id}/budget/items", headers=test_user_headers).json()
    lighting_item = next(b for b in bgt_items if b["item_name"] == "Fairy Lights & Lamps")
    assert lighting_item["estimated_amount"] == 35000.0
    assert "Plan Rescue" in lighting_item["notes"]

    # 8. Verify that emergency task was created
    tasks = client.get(f"/api/events/{event_id}/tasks", headers=test_user_headers).json()
    volunteer_task = next(t for t in tasks if "Recruit volunteer" in t["title"])
    assert volunteer_task["priority"] == "high"
    assert volunteer_task["category"] == "Volunteers"

    # 9. Verify audit history records
    hist_res = client.get(f"/api/events/{event_id}/rescue/history", headers=test_user_headers)
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) >= 1
    assert hist[0]["applied"] == 1
