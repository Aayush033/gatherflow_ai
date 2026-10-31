def test_user_data_isolation(client, test_user_headers, other_user_headers):
    """
    Verifies critical security release gate:
    One user MUST NOT access or modify another user's events, budgets, tasks, vendors, or chat history.
    """
    # 1. User A creates an event
    create_payload = {
        "title": "Aarav & Priya Wedding",
        "event_type": "wedding",
        "date": "2026-12-15",
        "location": "Jaipur Palace, Rajasthan",
        "guest_count": 250,
        "budget": 1500000.0,
        "currency": "INR",
        "theme": "Royal Rajasthani Heritage"
    }
    res_a = client.post("/api/events", json=create_payload, headers=test_user_headers)
    assert res_a.status_code == 201
    event_id = res_a.json()["id"]
    
    # User A adds a budget item
    bgt_a = client.post(
        f"/api/events/{event_id}/budget/items",
        json={"category": "Venue", "item_name": "Heritage Courtyard", "estimated_amount": 500000.0},
        headers=test_user_headers
    ).json()
    
    # User A adds a vendor
    vnd_a = client.post(
        f"/api/events/{event_id}/vendors",
        json={"name": "Palace Decorators", "category": "Decor", "quotation_amount": 100000.0},
        headers=test_user_headers
    ).json()
    
    # 2. User A can list and retrieve the event
    list_res_a = client.get("/api/events", headers=test_user_headers)
    assert any(e["id"] == event_id for e in list_res_a.json())
    
    get_res_a = client.get(f"/api/events/{event_id}", headers=test_user_headers)
    assert get_res_a.status_code == 200
    
    # 3. User B attempts to access User A's event -> Must be 404
    get_res_b = client.get(f"/api/events/{event_id}", headers=other_user_headers)
    assert get_res_b.status_code == 404
    
    # 4. User B lists events -> Must NOT see User A's event
    list_res_b = client.get("/api/events", headers=other_user_headers)
    assert not any(e["id"] == event_id for e in list_res_b.json())
    
    # 5. User B attempts to access User A's blueprint -> Must be 404
    bp_res_b = client.get(f"/api/events/{event_id}/blueprint", headers=other_user_headers)
    assert bp_res_b.status_code == 404
    
    # 6. User B attempts to access User A's budget items -> Must be 404
    bgt_res_b = client.get(f"/api/events/{event_id}/budget/items", headers=other_user_headers)
    assert bgt_res_b.status_code == 404
    
    # 7. User B attempts to access User A's vendors -> Must be 404
    vnd_res_b = client.get(f"/api/events/{event_id}/vendors", headers=other_user_headers)
    assert vnd_res_b.status_code == 404
    
    # 8. User B attempts to access User A's copilot chat messages -> Must be 404
    chat_res_b = client.get(f"/api/events/{event_id}/copilot/messages", headers=other_user_headers)
    assert chat_res_b.status_code == 404

    # 9. User B attempts to add a task to User A's event -> Must be 404
    task_res_b = client.post(
        f"/api/events/{event_id}/tasks",
        json={"title": "Malicious Task", "category": "General"},
        headers=other_user_headers
    )
    assert task_res_b.status_code == 404
    
    # 10. User B attempts to delete User A's event -> Must be 404
    del_res_b = client.delete(f"/api/events/{event_id}", headers=other_user_headers)
    assert del_res_b.status_code == 404
    
    # 11. User A verifies event is intact
    get_res_a_after = client.get(f"/api/events/{event_id}", headers=test_user_headers)
    assert get_res_a_after.status_code == 200

def test_unauthenticated_request_rejected(client):
    """
    Verifies that calls to protected event endpoints without a valid session
    are rejected with HTTP 401 Unauthorized.
    """
    res = client.get("/api/events")
    assert res.status_code == 401

def test_forged_session_token_rejected(client):
    """
    Verifies that supplying a forged, non-existent session token does NOT
    automatically grant access or create an identity with that token.
    """
    res = client.get("/api/events", headers={"X-Session-ID": "forged_non_existent_token_12345"})
    assert res.status_code == 401
