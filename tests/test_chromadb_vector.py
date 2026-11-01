from app.vector_db import (
    index_user_vendor,
    init_vector_db,
    search_knowledge_semantic,
    search_rescue_playbooks,
    search_vendors_text_similarity,
)


def test_chromadb_initialization_no_fake_vendors():
    """Verifies that ChromaDB initializes without seeding fake or invented vendor records."""
    init_vector_db()
    # No vendors should exist prior to user entry
    vendors = search_vendors_text_similarity("drone photography", event_id="evt_empty_test", n_results=3)
    assert len(vendors) == 0


def test_chromadb_knowledge_rag_retrieval():
    """Verifies retrieval of honest planning heuristics and suggestions."""
    init_vector_db()
    knowledge = search_knowledge_semantic("event budget distribution heuristic", n_results=3)
    assert len(knowledge) > 0
    assert any("budget" in k["content"].lower() or "allocation" in k["content"].lower() for k in knowledge)


def test_chromadb_rescue_playbook_retrieval():
    """
    Verifies crisis contingency playbook initialization and retrieval:
    1. All expected rescue records are initialized.
    2. A weather-contingency query returns actual stored playbook content.
    3. Returned guidance contains relevant stored information.
    4. Repeated initialization does not duplicate records.
    5. Other application collections remain unaffected.
    """
    from app.vector_db import GENERAL_RESCUE_PLAYBOOKS, get_chroma_client

    init_vector_db()
    client = get_chroma_client()
    rescue_col = client.get_collection("rescue_playbooks")
    initial_count = rescue_col.count()

    # 1. All expected rescue records are initialized
    assert initial_count == len(GENERAL_RESCUE_PLAYBOOKS)
    assert initial_count > 0

    # 2. A weather-contingency query returns actual stored playbook content
    playbooks = search_rescue_playbooks("rain forecast outdoor weather contingency", n_results=2)
    assert len(playbooks) > 0

    # 3. Returned guidance contains relevant stored information
    assert any(
        "weather" in p["guidance"].lower()
        or "indoor" in p["guidance"].lower()
        or "contingency" in p["guidance"].lower()
        for p in playbooks
    )
    first_match = playbooks[0]
    assert first_match["id"]
    assert first_match["scenario"]
    assert len(first_match["guidance"]) > 20

    # 4. Repeated initialization does not duplicate records
    init_vector_db()
    assert rescue_col.count() == initial_count

    # 5. Other application collections remain unaffected
    vendor_col = client.get_collection("vendor_catalog")
    initial_vendor_count = vendor_col.count()
    init_vector_db()
    assert vendor_col.count() == initial_vendor_count


def test_chromadb_user_vendor_indexing_and_event_isolation():
    """
    Verifies that user vendor indexing works and records are strictly scoped to the event.
    Records from Event A must NOT appear in search results for Event B!
    """
    init_vector_db()
    event_a = "evt_wedding_alpha_100"
    event_b = "evt_birthday_beta_200"

    custom_vendor = {
        "id": "vnd_test_custom_001",
        "name": "Bespoke Royal Fireworks",
        "category": "Entertainment",
        "notes": "Eco-friendly cold pyro stage sparklers and green fireworks display for grand entry",
        "quotation_amount": 25000.0,
        "event_id": event_a,
        "user_id": "usr_user_1",
    }
    index_user_vendor(custom_vendor, event_id=event_a, user_id="usr_user_1")

    # 1. Search within Event A -> Must find the vendor
    results_a = search_vendors_text_similarity("cold pyro sparklers fireworks", event_id=event_a, n_results=3)
    assert any(r["id"] == "vnd_test_custom_001" for r in results_a)

    # 2. Search within Event B -> Must NOT find the vendor (Strict Isolation!)
    results_b = search_vendors_text_similarity("cold pyro sparklers fireworks", event_id=event_b, n_results=3)
    assert not any(r["id"] == "vnd_test_custom_001" for r in results_b)


def test_semantic_vendor_search_api_endpoint(client, test_user_headers):
    """
    Verifies the vendor text similarity search endpoint returns user-entered vendors for that event.
    """
    # 1. Create an event
    event_payload = {
        "title": "ChromaDB Test Gala",
        "event_type": "community",
        "date": "2026-11-20",
        "location": "Bengaluru",
        "guest_count": 200,
        "budget": 300000.0,
        "currency": "INR",
    }
    create_resp = client.post("/api/events", json=event_payload, headers=test_user_headers)
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # 2. Initially empty state (truthful: no fake marketplace data)
    initial_search = client.get(
        f"/api/events/{event_id}/vendors/semantic-search?q=vegan+organic+farm+to+table", headers=test_user_headers
    )
    assert initial_search.status_code == 200
    assert initial_search.json() == []

    # 3. Add actual user vendor
    vendor_payload = {
        "name": "Green Earth Farm to Table",
        "category": "Catering",
        "quotation_amount": 75000.0,
        "status": "quoted",
        "notes": "100% organic farm-to-table vegan dishes with sustainable packaging",
    }
    client.post(f"/api/events/{event_id}/vendors", json=vendor_payload, headers=test_user_headers)

    # 4. Search again -> Now returns the user-entered vendor
    search_resp = client.get(
        f"/api/events/{event_id}/vendors/semantic-search?q=vegan+organic+farm+to+table", headers=test_user_headers
    )
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) > 0
    assert any("green earth" in r["name"].lower() for r in results)
