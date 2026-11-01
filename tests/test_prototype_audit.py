from app.config import settings


def test_prototype_complete_event_lifecycle(client, test_user_headers, other_user_headers):
    """
    High-level Prototype & Submission Audit Test:
    Verifies the end-to-end event planning lifecycle across:
    1. Security & Evaluator Session Authentication
    2. Event Creation & Ownership Scoping
    3. 4-Tier Financial Math & Vendor-Budget Sync
    4. Deterministic What-If Scenario Simulation
    5. Isolated ChromaDB Vector Indexing
    6. Multi-tenant Boundary Enforcement
    """
    # 1. Verify Model Integrity
    health = client.get("/api/health").json()
    assert health["ai"]["model"] == "gemini-3.8-flash"
    assert health["database"]["status"] == "healthy"

    # 2. Verify Evaluator Passcode Authentication
    bad_auth = client.post("/api/auth/evaluator-login", json={"passcode": "wrong-code"})
    assert bad_auth.status_code == 401

    good_auth = client.post("/api/auth/evaluator-login", json={"passcode": settings.EVALUATOR_PASSCODE})
    assert good_auth.status_code == 200
    assert "session_token" not in good_auth.json()

    # 3. Create Event
    ev_resp = client.post(
        "/api/events",
        json={
            "title": "Grand Royal Wedding Gala",
            "event_type": "wedding",
            "date": "2026-12-25",
            "time_details": "18:00 to 23:00",
            "location": "Udaipur Palace Courtyard",
            "guest_count": 250,
            "budget": 1500000.0,
            "currency": "INR",
            "theme": "Heritage Palace Elegance",
            "cultural_preferences": "Traditional Rajasthani Royal banquet",
            "priorities_constraints": "High quality photography and gourmet live counters",
        },
        headers=test_user_headers,
    )
    assert ev_resp.status_code == 201
    event = ev_resp.json()
    event_id = event["id"]
    assert event["budget"] == 1500000.0
    assert event["guest_count"] == 250

    # 4. Add Budget Line Items
    b1 = client.post(
        f"/api/events/{event_id}/budget/items",
        json={
            "category": "Catering",
            "item_name": "Royal Banquet Buffet",
            "estimated_amount": 500000.0,
            "status": "planned",
        },
        headers=test_user_headers,
    ).json()

    client.post(
        f"/api/events/{event_id}/budget/items",
        json={
            "category": "Photography",
            "item_name": "Cinematic 4K Drone & Candid",
            "estimated_amount": 250000.0,
            "status": "planned",
        },
        headers=test_user_headers,
    ).json()

    # Check baseline summary: Initial AI plan seeded items (300,000) + 750,000 = 1,050,000
    s0 = client.get(f"/api/events/{event_id}/budget/summary", headers=test_user_headers).json()
    assert s0["total_estimated"] == 1050000.0
    assert s0["total_committed"] == 0.0
    assert s0["total_actual"] == 0.0

    # 5. Add Vendor with Quotation linked to Catering
    v1 = client.post(
        f"/api/events/{event_id}/vendors",
        json={
            "name": "Maharaja Culinary Services",
            "category": "Catering",
            "contact_person": "Vikram Singh",
            "contact_phone": "+91 99887 76655",
            "quotation_amount": 480000.0,
            "status": "quoted",
            "linked_budget_item_id": b1["id"],
        },
        headers=test_user_headers,
    ).json()

    # Quotation recorded, but committed must STILL be 0
    s1 = client.get(f"/api/events/{event_id}/budget/summary", headers=test_user_headers).json()
    assert s1["total_quoted"] == 480000.0
    assert s1["total_committed"] == 0.0

    # Confirm Vendor -> Committed now becomes 480,000, Actual remains 0
    client.patch(f"/api/events/{event_id}/vendors/{v1['id']}", json={"status": "confirmed"}, headers=test_user_headers)

    s2 = client.get(f"/api/events/{event_id}/budget/summary", headers=test_user_headers).json()
    assert s2["total_committed"] == 480000.0
    assert s2["total_actual"] == 0.0
    assert s2["remaining_from_committed"] == (1500000.0 - 480000.0)

    # 6. Test What-If Scenario Calculation
    scenario = client.post(
        f"/api/events/{event_id}/budget/scenario",
        json={
            "guest_count_delta": 50,
            "budget_delta_percent": -10.0,
            "additional_expense": 25000.0,
            "notes": "Testing guest expansion with 10% budget tightening",
        },
        headers=test_user_headers,
    ).json()

    assert scenario["original_budget"] == 1500000.0
    assert scenario["projected_budget"] == 1350000.0  # 1.5M - 10%
    assert scenario["original_guest_count"] == 250
    assert scenario["projected_guest_count"] == 300
    assert "deterministic_analysis" in scenario
    assert len(scenario["deterministic_analysis"]) > 20

    # 7. Add Task & Check Progress
    client.post(
        f"/api/events/{event_id}/tasks",
        json={
            "title": "Sign palace rental contract",
            "category": "Venue",
            "priority": "critical",
            "due_date": "2026-11-01",
            "status": "completed",
        },
        headers=test_user_headers,
    ).json()

    client.post(
        f"/api/events/{event_id}/tasks",
        json={
            "title": "Review catering menu draft",
            "category": "Catering",
            "priority": "high",
            "due_date": "2026-11-15",
            "status": "todo",
        },
        headers=test_user_headers,
    ).json()

    bp = client.get(f"/api/events/{event_id}/blueprint", headers=test_user_headers).json()
    assert bp["task_summary"]["total_tasks"] == 4  # 2 seeded checklist tasks + 2 user tasks
    assert bp["task_summary"]["completed_tasks"] == 1
    assert bp["task_summary"]["progress_percentage"] == 25.0

    # 8. Semantic ChromaDB Vendor Search Scoped to User & Event
    search_res = client.get(
        f"/api/events/{event_id}/vendors/semantic-search?q=Catering", headers=test_user_headers
    ).json()
    assert isinstance(search_res, list)
    # The user's confirmed vendor should be indexed in ChromaDB
    vendor_names = [v["name"] for v in search_res]
    assert "Maharaja Culinary Services" in vendor_names

    # 9. Verify Multi-Tenant Isolation: other_user CANNOT access this event or search this vendor
    unauth_bp = client.get(f"/api/events/{event_id}/blueprint", headers=other_user_headers)
    assert unauth_bp.status_code == 404

    unauth_search = client.get(f"/api/events/{event_id}/vendors/semantic-search?q=Catering", headers=other_user_headers)
    assert unauth_search.status_code == 404
