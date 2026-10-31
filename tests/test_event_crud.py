def test_event_crud_and_validation(client, test_user_headers):
    """Verifies event creation, retrieval, updates, and input validation."""
    # 1. Invalid input: negative budget
    invalid_payload = {
        "title": "Invalid Birthday",
        "event_type": "birthday",
        "date": "2026-11-20",
        "location": "Community Center",
        "guest_count": 50,
        "budget": -1000.0 # Invalid!
    }
    res_inv = client.post("/api/events", json=invalid_payload, headers=test_user_headers)
    assert res_inv.status_code == 422 # Pydantic validation error
    
    # 2. Valid event creation
    valid_payload = {
        "title": "Vivaan's 10th Birthday Adventure",
        "event_type": "birthday",
        "date": "2026-11-20",
        "location": "Adventure Park, Bengaluru",
        "guest_count": 40,
        "budget": 75000.0,
        "currency": "INR",
        "theme": "Superheroes & Outdoor Games",
        "cultural_preferences": "Vegetarian snacks, nut-free cake"
    }
    res = client.post("/api/events", json=valid_payload, headers=test_user_headers)
    assert res.status_code == 201
    created = res.json()
    event_id = created["id"]
    assert created["title"] == valid_payload["title"]
    assert created["guest_count"] == 40
    assert created["budget"] == 75000.0
    
    # 3. Update event parameters
    update_payload = {
        "guest_count": 50,
        "budget": 90000.0
    }
    patch_res = client.patch(f"/api/events/{event_id}", json=update_payload, headers=test_user_headers)
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["guest_count"] == 50
    assert updated["budget"] == 90000.0
    
    # 4. Delete event
    del_res = client.delete(f"/api/events/{event_id}", headers=test_user_headers)
    assert del_res.status_code == 204
    
    # Confirm deletion
    get_res = client.get(f"/api/events/{event_id}", headers=test_user_headers)
    assert get_res.status_code == 404
