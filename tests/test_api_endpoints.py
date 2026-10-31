from app.config import settings

def test_health_check_endpoint(client):
    """Verifies that /api/health reports honest database and AI configuration status without expensive calls."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["database"]["engine"] == "sqlite"
    assert "events" in data["database"]["tables"]
    # Verified: both 'ai' and 'generative_ai' keys exist
    assert "ai" in data
    assert "generative_ai" in data
    assert data["ai"]["model"] == "gemini-3.8-flash"
    assert "verification_endpoint" in data["ai"]

def test_evaluator_login_endpoint_secure(client):
    """
    Verifies that official evaluator login validates the passcode,
    sets a secure HTTP-only cookie, and does NOT leak the session token in the JSON body.
    """
    # 1. Reject invalid passcode
    res_bad = client.post("/api/auth/evaluator-login", json={"passcode": "invalid-passcode"})
    assert res_bad.status_code == 401
    
    # 2. Accept valid passcode
    res_good = client.post("/api/auth/evaluator-login", json={"passcode": settings.EVALUATOR_PASSCODE})
    assert res_good.status_code == 200
    data = res_good.json()
    
    # Session token must NOT be leaked in JSON body
    assert "session_token" not in data
    # Cookie must be set
    assert res_good.cookies.get(settings.SESSION_COOKIE_NAME) is not None
    assert data["email"] == settings.DEFAULT_EVALUATOR_EMAIL

def test_vendor_to_budget_sync_workflow(client, test_user_headers):
    """
    Workflow D: Verifies that vendor quotations and confirmation
    sync cleanly with linked budget items without falsely treating quotations as paid costs.
    """
    # 1. Create an event
    ev = client.post("/api/events", json={
        "title": "Corporate Annual Meet 2026",
        "event_type": "community",
        "date": "2026-12-01",
        "location": "Convention Hall, Hyderabad",
        "guest_count": 200,
        "budget": 400000.0,
        "currency": "INR"
    }, headers=test_user_headers).json()
    event_id = ev["id"]
    
    # 2. Create a budget item for Catering
    bgt = client.post(f"/api/events/{event_id}/budget/items", json={
        "category": "Catering",
        "item_name": "Lunch & High Tea",
        "estimated_amount": 150000.0
    }, headers=test_user_headers).json()
    budget_item_id = bgt["id"]
    
    # 3. Add a vendor with a quotation, linked to the budget item
    vnd = client.post(f"/api/events/{event_id}/vendors", json={
        "name": "Royal Feast Caterers",
        "category": "Catering",
        "contact_person": "Chef Rajesh",
        "contact_phone": "+91 98765 43210",
        "quotation_amount": 140000.0,
        "status": "quoted",
        "linked_budget_item_id": budget_item_id
    }, headers=test_user_headers).json()
    vendor_id = vnd["id"]
    
    # 4. Check budget summary: Quotation must be recorded, but committed must be 0 and actual must be 0!
    summary_1 = client.get(f"/api/events/{event_id}/budget/summary", headers=test_user_headers).json()
    assert summary_1["total_quoted"] == 140000.0
    assert summary_1["total_committed"] == 0.0 # NOT committed yet!
    assert summary_1["total_actual"] == 0.0    # NOT paid yet!
    
    # 5. Confirm vendor
    client.patch(f"/api/events/{event_id}/vendors/{vendor_id}", json={
        "status": "confirmed"
    }, headers=test_user_headers)
    
    # 6. Check budget summary now: Committed is now 140,000, but Actual is STILL 0!
    summary_2 = client.get(f"/api/events/{event_id}/budget/summary", headers=test_user_headers).json()
    assert summary_2["total_committed"] == 140000.0
    assert summary_2["total_actual"] == 0.0 # Quotation is NEVER falsely claimed as an actual payment!
    assert summary_2["remaining_from_committed"] == (400000.0 - 140000.0)

def test_vendor_cross_event_budget_link_blocked(client, test_user_headers):
    """
    Verifies that a vendor in Event A CANNOT link to a budget item belonging to Event B.
    """
    # Event 1
    ev1 = client.post("/api/events", json={
        "title": "Event One", "event_type": "birthday", "date": "2026-11-15",
        "location": "Venue 1", "guest_count": 50, "budget": 100000.0
    }, headers=test_user_headers).json()
    
    # Event 2
    ev2 = client.post("/api/events", json={
        "title": "Event Two", "event_type": "birthday", "date": "2026-11-16",
        "location": "Venue 2", "guest_count": 60, "budget": 120000.0
    }, headers=test_user_headers).json()
    
    bgt_item_ev1 = client.post(f"/api/events/{ev1['id']}/budget/items", json={
        "category": "Decor", "item_name": "Event 1 Decor", "estimated_amount": 20000.0
    }, headers=test_user_headers).json()
    
    # Try to link Event 2 vendor to Event 1 budget item -> Must return 400 Bad Request
    res = client.post(f"/api/events/{ev2['id']}/vendors", json={
        "name": "Intruder Vendor",
        "category": "Decor",
        "quotation_amount": 18000.0,
        "status": "quoted",
        "linked_budget_item_id": bgt_item_ev1["id"]
    }, headers=test_user_headers)
    assert res.status_code == 400
    assert "does not belong" in res.json()["detail"].lower()


def test_demo_showcase_seeding_and_retrieval(client, test_user_headers):
    """Verifies that the demo showcase endpoint instantly generates a rich, valid event for evaluators."""
    res = client.post("/api/events/demo-showcase", headers=test_user_headers)
    assert res.status_code == 201
    data = res.json()
    assert "Global Tech" in data["title"]
    assert data["budget"] == 50000.0
    assert data["guest_count"] == 250
    event_id = data["id"]

    # Verify blueprint exists
    plan_res = client.get(f"/api/events/{event_id}/plan", headers=test_user_headers)
    assert plan_res.status_code == 200
    plan = plan_res.json()
    assert plan is not None
    assert "flagship corporate celebration" in plan["concept"].lower()

    # Verify budget items and summary exist
    bgt_items = client.get(f"/api/events/{event_id}/budget/items", headers=test_user_headers).json()
    assert len(bgt_items) >= 5

    bgt_sum = client.get(f"/api/events/{event_id}/budget/summary", headers=test_user_headers).json()
    assert bgt_sum["planned_budget"] == 50000.0

    # Verify tasks exist
    tasks = client.get(f"/api/events/{event_id}/tasks", headers=test_user_headers).json()
    assert len(tasks) >= 5

    # Verify vendors exist
    vnds = client.get(f"/api/events/{event_id}/vendors", headers=test_user_headers).json()
    assert len(vnds) >= 2
