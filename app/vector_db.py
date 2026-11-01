"""
GatherFlow AI - ChromaDB Vector Database Layer
Provides persistent similarity search for:
1. Event-specific user vendor records (lexical & n-gram text similarity)
2. Event planning knowledge retrieval (General heuristics & suggestions for Copilot)
3. Emergency contingency & crisis rescue playbooks

Note on Embeddings:
Uses deterministic 256-dimensional n-gram token hashing. This provides fast, offline
approximate lexical and phrase similarity matching without transmitting data to external
embedding APIs.
"""

import hashlib
import logging
import math
from pathlib import Path
from typing import Any

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from app.config import settings

logger = logging.getLogger("gatherflow.vector_db")


class GatherFlowEmbeddingFunction(EmbeddingFunction):
    """
    Deterministic, offline vector embedding function.
    Generates normalized 256-dimensional embeddings using unigram & bigram
    hashing for approximate text similarity search.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim

    @staticmethod
    def name() -> str:
        return "gatherflow_text_similarity"

    def get_config(self) -> dict:
        return {"dim": self.dim}

    @classmethod
    def build_from_config(cls, config: dict):
        return cls(dim=config.get("dim", 256))

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: list[list[float]] = []
        for text in input:
            vec = [0.0] * self.dim
            tokens = text.lower().replace("-", " ").replace(",", " ").split()

            # Unigrams
            for t in tokens:
                clean = "".join(ch for ch in t if ch.isalnum())
                if clean:
                    idx = int(hashlib.md5(clean.encode()).hexdigest(), 16) % self.dim
                    vec[idx] += 1.0

            # Bigrams for phrase capture
            for i in range(len(tokens) - 1):
                bg = f"{tokens[i]}_{tokens[i + 1]}"
                idx = int(hashlib.md5(bg.encode()).hexdigest(), 16) % self.dim
                vec[idx] += 1.5

            # L2 Normalization
            norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            embeddings.append([round(x / norm, 6) for x in vec])
        return embeddings


_embedding_fn = GatherFlowEmbeddingFunction(dim=256)
_client: Any | None = None


def get_chroma_client(persist_path: Path | None = None) -> Any:
    """Returns singleton ChromaDB persistent client or test-injected client."""
    global _client
    if _client is None:
        target_path = persist_path or settings.CHROMA_PERSIST_PATH
        target_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(target_path))
    return _client


def set_chroma_client(client: Any | None):
    """Allows test fixtures to inject an isolated ephemeral client."""
    global _client
    _client = client


# ─────────────────────────────────────────────────────────────
# DOMAIN KNOWLEDGE & RESCUE PLAYBOOKS (General Suggestions & Heuristics)
# ─────────────────────────────────────────────────────────────

# Explicitly labeled as general industry heuristics, NOT universal mandates or statutory rules.
GENERAL_KNOWLEDGE_SUGGESTIONS = [
    {
        "id": "know_budget_heuristic_allocation",
        "title": "General Budget Distribution Heuristic",
        "doc": "Typical industry rule of thumb for event budgeting (subject to local custom and preference): Venue & Food/Beverage (~40-45%), Photography (~10-15%), Decor & Styling (~15%), Entertainment & Sound (~10%), Discretionary Contingency Reserve (~10-15%).",
        "category": "budgeting",
    },
    {
        "id": "know_weather_contingency_guideline",
        "title": "Outdoor Event Weather Contingency Guideline",
        "doc": "Guideline for outdoor gatherings: Contract an on-site covered or indoor backup option where feasible. Consider weatherproofing measures (industrial canopies, fans, heaters) and keep electrical distribution cabling safely elevated on dry risers.",
        "category": "weather_contingency",
    },
    {
        "id": "know_dietary_guideline",
        "title": "Dietary Inclusivity and Accessibility Suggestions",
        "doc": "Planning suggestion: Provide vegetarian, vegan, and allergen-labelled food stations. Ensure step-free entrance access and clearly identifiable accessible facilities for attendees with mobility requirements.",
        "category": "hospitality",
    },
    {
        "id": "know_sound_curfew_notice",
        "title": "Municipal Sound Curfew General Advisory",
        "doc": "Advisory notice: Many municipal jurisdictions and residential zones enforce amplified sound curfews (often 10:00 PM). Verify specific local city permits and venue policies to prevent disruptions.",
        "category": "compliance",
    },
    {
        "id": "know_vendor_payment_milestone_suggestion",
        "title": "Vendor Contract Milestone Payment Suggestions",
        "doc": "Industry practice suggestion: Avoid full advance payments where possible. Consider phased milestone payments (e.g. booking advance, mid-point check-in, event day commencement, and post-delivery sign-off) aligned with deliverables.",
        "category": "vendor_management",
    },
]

GENERAL_RESCUE_PLAYBOOKS = [
    {
        "id": "rescue_venue_cancellation",
        "scenario": "Venue unavailable on short notice or scheduling conflict",
        "doc": "Suggested Venue Recovery Steps: 1. Contact pre-screened alternative venues with matching capacity. 2. Consider clubhouses, event ballrooms, or hybrid indoor/outdoor locations. 3. Adjust seating format (e.g. lounge cocktail style) if footprint differs. 4. Issue concise broadcast to guests with updated directions.",
        "playbook_json": '{"priority_actions": ["Filter backup venues by guest capacity", "Adapt seating layout if square footage differs", "Send prompt update broadcast to guests"]}',
    },
    {
        "id": "rescue_budget_reduction",
        "scenario": "Target budget reduced after initial planning commenced",
        "doc": "Suggested Budget Realignment Steps: 1. Streamline high-cost custom catering items to focused core offerings. 2. Emphasize ambient lighting and local seasonal decor over complex floral imports. 3. Consolidate printed materials into digital schedules. 4. Focus photography coverage on headline ceremonial milestones.",
        "playbook_json": '{"priority_actions": ["Focus food and beverage to core selections", "Use architectural uplighting in place of heavy decor", "Prioritize key photographer coverage hours"]}',
    },
    {
        "id": "rescue_guest_surge",
        "scenario": "Guest count exceeds original estimate",
        "doc": "Suggested Guest Surge Recovery Steps: 1. Confer with catering to expand buffet throughput or increase replenishment speed. 2. Add roving appetizer service to distribute initial dining demand. 3. Arrange additional rental seating. 4. Expand welcome and parking coordination.",
        "playbook_json": '{"priority_actions": ["Coordinate with catering for higher throughput stations", "Add roving appetizer service", "Confirm supplementary rental seating", "Enhance guest welcome staffing"]}',
    },
    {
        "id": "rescue_weather_disruption",
        "scenario": "Adverse weather forecast for scheduled outdoor event",
        "doc": "Suggested Weather Recovery Steps: 1. Confirm activation timeline for venue indoor contingency space. 2. Deploy waterproof side-coverings and covered walkways. 3. Protect electrical and audio cabling with elevated conduits. 4. Prepare entrance umbrella stands and towel service.",
        "playbook_json": '{"priority_actions": ["Activate indoor hall contingency agreement", "Secure electrical connections with water-resistant enclosures", "Deploy covered walkways and umbrellas"]}',
    },
]


def init_vector_db():
    """
    Initializes ChromaDB collections for user vendor similarity search,
    general knowledge heuristics, and rescue playbooks.
    Note: NO fake or invented vendors are seeded.
    """
    try:
        client = get_chroma_client()

        # 1. User Vendors Collection (scoped by event/user, empty by default)
        client.get_or_create_collection(
            name="vendor_catalog",
            embedding_function=_embedding_fn,
            metadata={"description": "User-entered vendor records with text similarity search"},
        )

        # 2. Planning Knowledge Collection (general heuristics)
        know_col = client.get_or_create_collection(
            name="event_knowledge",
            embedding_function=_embedding_fn,
            metadata={"description": "Event planning heuristics and general suggestions"},
        )
        if know_col.count() == 0:
            know_col.add(
                ids=[k["id"] for k in GENERAL_KNOWLEDGE_SUGGESTIONS],
                documents=[f"{k['title']}: {k['doc']}" for k in GENERAL_KNOWLEDGE_SUGGESTIONS],
                metadatas=[{"title": k["title"], "category": k["category"]} for k in GENERAL_KNOWLEDGE_SUGGESTIONS],
            )
            logger.info("Initialized ChromaDB event_knowledge with %d suggestions", len(GENERAL_KNOWLEDGE_SUGGESTIONS))

        # 3. Rescue Playbooks Collection
        rescue_col = client.get_or_create_collection(
            name="rescue_playbooks",
            embedding_function=_embedding_fn,
            metadata={"description": "General crisis recovery suggestions and contingency playbooks"},
        )
        if rescue_col.count() == 0:
            rescue_col.add(
                ids=[r["id"] for r in GENERAL_RESCUE_PLAYBOOKS],
                documents=[f"Scenario: {r['scenario']}. Strategy: {r['doc']}" for r in GENERAL_RESCUE_PLAYBOOKS],
                metadatas=[
                    {"scenario": r["scenario"], "playbook_json": r["playbook_json"]} for r in GENERAL_RESCUE_PLAYBOOKS
                ],
            )
            logger.info("Initialized ChromaDB rescue_playbooks with %d playbooks", len(GENERAL_RESCUE_PLAYBOOKS))

    except Exception as e:
        logger.error("Failed to initialize ChromaDB: %s", e)
        raise


def index_user_vendor(vendor_dict: dict[str, Any], event_id: str | None = None, user_id: str | None = None):
    """
    Indexes a user-entered vendor in ChromaDB, strictly scoped to the user's event.
    No cross-user or cross-event leakage.
    """
    client = get_chroma_client()
    vendor_col = client.get_or_create_collection(name="vendor_catalog", embedding_function=_embedding_fn)
    vid = vendor_dict["id"]
    name = vendor_dict.get("name", "Vendor")
    category = vendor_dict.get("category", "General")
    notes = vendor_dict.get("notes", "") or ""
    quotation = float(vendor_dict.get("quotation_amount", 0.0) or 0.0)
    eid = event_id or vendor_dict.get("event_id", "")
    uid = user_id or vendor_dict.get("user_id", "")

    doc = f"{name} ({category}): {notes}. Quote: {quotation}"

    vendor_col.upsert(
        ids=[vid],
        documents=[doc],
        metadatas=[{"name": name, "category": category, "event_id": eid, "user_id": uid, "quotation": quotation}],
    )


def delete_user_vendor(vendor_id: str):
    """Removes a vendor record from ChromaDB when deleted by the user."""
    try:
        client = get_chroma_client()
        vendor_col = client.get_or_create_collection(name="vendor_catalog", embedding_function=_embedding_fn)
        vendor_col.delete(ids=[vendor_id])
    except Exception as e:
        logger.warning(f"Could not delete vendor {vendor_id} from vector store: {e}")


def search_vendors_text_similarity(
    query: str, event_id: str, category: str | None = None, n_results: int = 5
) -> list[dict[str, Any]]:
    """
    Performs text similarity search across the user's saved vendors for this specific event.
    Only returns records belonging to the event specified.
    """
    client = get_chroma_client()
    vendor_col = client.get_or_create_collection(name="vendor_catalog", embedding_function=_embedding_fn)

    if vendor_col.count() == 0:
        return []

    # Strictly scope search by event_id
    if category:
        where_filter = {"$and": [{"event_id": {"$eq": event_id}}, {"category": {"$eq": category}}]}
    else:
        where_filter = {"event_id": {"$eq": event_id}}

    try:
        results = vendor_col.query(
            query_texts=[query], n_results=min(n_results, max(1, vendor_col.count())), where=where_filter
        )
    except Exception as e:
        logger.warning("Similarity search error in vendor_catalog: %s", e)
        return []

    items = []
    if results and results.get("ids") and results["ids"][0]:
        for i, vid in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            doc = results["documents"][0][i] if results.get("documents") else ""
            dist = results["distances"][0][i] if results.get("distances") else 0.0
            items.append(
                {
                    "id": vid,
                    "name": metadata.get("name", vid),
                    "category": metadata.get("category", "General"),
                    "description": doc,
                    "metadata": metadata,
                    "match_score": round(max(0.0, 1.0 - dist), 3),
                }
            )
    return items


# Backward-compatible alias accurately documented
search_vendors_semantic = search_vendors_text_similarity


def search_knowledge_semantic(query: str, n_results: int = 3) -> list[dict[str, Any]]:
    """
    Retrieves relevant planning suggestions and heuristics using text similarity.
    Used for context enrichment in Copilot.
    """
    client = get_chroma_client()
    know_col = client.get_or_create_collection(name="event_knowledge", embedding_function=_embedding_fn)
    if know_col.count() == 0:
        init_vector_db()
        know_col = client.get_or_create_collection(name="event_knowledge", embedding_function=_embedding_fn)

    if know_col.count() == 0:
        return []

    try:
        results = know_col.query(query_texts=[query], n_results=min(n_results, max(1, know_col.count())))
    except Exception as e:
        logger.warning("Retrieval error in event_knowledge: %s", e)
        return []

    items = []
    if results and results.get("ids") and results["ids"][0]:
        for i, kid in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            doc = results["documents"][0][i] if results.get("documents") else ""
            items.append(
                {
                    "id": kid,
                    "title": metadata.get("title", ""),
                    "content": doc,
                    "category": metadata.get("category", ""),
                }
            )
    return items


def search_rescue_playbooks(scenario_text: str, n_results: int = 2) -> list[dict[str, Any]]:
    """
    Retrieves general contingency suggestions matching the crisis scenario.
    """
    client = get_chroma_client()
    rescue_col = client.get_or_create_collection(name="rescue_playbooks", embedding_function=_embedding_fn)
    if rescue_col.count() == 0:
        init_vector_db()
        rescue_col = client.get_or_create_collection(name="rescue_playbooks", embedding_function=_embedding_fn)

    if rescue_col.count() == 0:
        return []

    try:
        results = rescue_col.query(query_texts=[scenario_text], n_results=min(n_results, max(1, rescue_col.count())))
    except Exception as e:
        logger.warning("Retrieval error in rescue_playbooks: %s", e)
        return []

    items = []
    if results and results.get("ids") and results["ids"][0]:
        for i, rid in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
            doc = results["documents"][0][i] if results.get("documents") else ""
            items.append(
                {
                    "id": rid,
                    "scenario": metadata.get("scenario", ""),
                    "guidance": doc,
                    "playbook_json": metadata.get("playbook_json", "{}"),
                }
            )
    return items
