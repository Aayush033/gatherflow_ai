# ✦ GatherFlow AI — GenAI Event Planning Studio 🎉

> **Prompt Wars 2026 Submission** — An autonomous event planning studio powered by Google Gemini 3.8-Flash, ChromaDB vector search, and 100% deterministic financial logic.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Gemini 3.8 Flash](https://img.shields.io/badge/Google_Gemini-3.8--Flash-4285F4?logo=google)](https://ai.google.dev)
[![Tests](https://img.shields.io/badge/Tests-22%2F22_Passed-brightgreen?logo=pytest)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🌟 What is GatherFlow AI?

GatherFlow AI is a **full-stack GenAI-powered event planning studio** that helps you plan weddings, corporate galas, community celebrations, and any event — from initial vision to stress-free execution.

### Key Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Blueprint Generator** | Gemini 3.8-Flash auto-generates theme concepts, phase milestones, prioritized checklists, and Next Best Actions with real-time health scoring |
| 💰 **Budget & What-If Studio** | Track Estimated → Quoted → Committed → Paid costs with 100% deterministic arithmetic. Simulate guest surges or budget cuts instantly |
| 🔍 **ChromaDB Vector Search** | Semantic vendor discovery scoped per-event using ChromaDB RAG pipeline |
| 🚨 **Plan Rescue AI** | When disruptions strike (vendor cancellation, budget cuts, guest surge), generate and apply an adaptive recovery plan in 1 click |
| 💬 **AI Copilot** | Conversational assistant with full event context — ask anything about your budget, vendors, timeline, or get suggestions |
| 🌐 **7 Languages** | English, Hindi, Spanish, French, German, Chinese, Arabic with RTL support |
| 🔒 **Secure Sessions** | HTTP-only cookies, 256-bit random tokens, strict user/event data isolation |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (tested on 3.12, 3.13, 3.14)
- Google Gemini API key

### Setup & Run

```bash
# 1. Clone the repository
git clone https://github.com/Aayush033/gatherflow_ai.git
cd gatherflow_ai

# 2. Create & activate virtual environment
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env   # Windows
cp .env.example .env     # macOS/Linux
# Edit .env → set GEMINI_API_KEY=your_key

# 5. Start the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Open browser → http://localhost:8000
```

### One-Click Demo
Click **"🌟 Load Demo Event"** on the home screen to instantly load a pre-configured showcase event with AI-generated blueprint, budget items, tasks, and vendors.

---

## 🏗️ Architecture

```
gatherflow_ai/
├── app/
│   ├── main.py              # FastAPI app, CORS, security middleware
│   ├── config.py            # Central config from environment
│   ├── database.py          # SQLite with WAL mode & foreign keys
│   ├── vector_db.py         # ChromaDB vector layer (event-scoped RAG)
│   ├── schemas.py           # Pydantic v2 schemas
│   ├── auth_deps.py         # Secure session validation
│   ├── routers/
│   │   ├── auth.py          # Evaluator auth & token generation
│   │   ├── events.py        # Event CRUD & AI plan orchestration
│   │   ├── blueprint.py     # Blueprint dashboard & health scoring
│   │   ├── budget.py        # Budget CRUD, summaries & scenario math
│   │   ├── tasks.py         # Task timeline & progress metrics
│   │   ├── vendors.py       # Vendor management with auto-sync
│   │   ├── rescue.py        # Plan Rescue AI with atomic updates
│   │   ├── copilot.py       # Conversational AI with RAG context
│   │   └── health.py        # Health check & AI verification
│   └── services/
│       ├── ai_service.py    # Gemini SDK with model fallback cascade
│       ├── budget_service.py# Deterministic financial calculations
│       ├── task_service.py  # Progress & overdue detection
│       └── rescue_service.py# Transaction-consistent rescue apply
├── static/                  # Responsive SPA (HTML5, CSS, Vanilla JS)
│   ├── index.html           # Single-page planning studio
│   ├── css/main.css         # Dark glassmorphism design
│   └── js/app.js            # App controller with i18n & markdown
├── tests/                   # 22 automated tests (~1.8s, fully offline)
├── Dockerfile               # Production container (Python 3.11-slim)
├── requirements.txt         # Pinned dependencies
├── .env.example             # Environment template
└── LICENSE                  # MIT License
```

---

## 🧪 Testing

```bash
# Run all 22 tests (fully offline, no API quota consumed)
python -m pytest tests/ -v

# ✅ 22/22 PASSED in ~1.8s
```

| Test Suite | Tests | What It Verifies |
|-----------|-------|-----------------|
| `test_api_endpoints.py` | 5 | Health check, evaluator auth, vendor sync, cross-event blocking, demo seeding |
| `test_budget_math.py` | 3 | Deterministic arithmetic, classifications, over-budget alerts |
| `test_chromadb_vector.py` | 5 | Vector indexing, scoped search, truthful empty states, event isolation |
| `test_event_crud.py` | 1 | Pydantic validation, persistence, deletion |
| `test_rescue_workflow.py` | 1 | Plan Rescue proposal generation & atomic apply |
| `test_tasks_and_progress.py` | 3 | Overdue date math, progress calculation |
| `test_user_isolation.py` | 3 | Multi-tenant boundaries, forged token rejection |
| `test_prototype_audit.py` | 1 | End-to-end event lifecycle audit |

---

## 🐳 Deployment

### Docker
```bash
docker build -t gatherflow-ai .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key gatherflow-ai
```

### Google Cloud Run
```bash
gcloud run deploy gatherflow-ai \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=your_key,ENVIRONMENT=production"
```

---

## 🛡️ Security & Compliance

- **Server-side API key** — Gemini key loaded from `.env`, never exposed to frontend
- **HTTP-only cookies** — 256-bit cryptographic session tokens
- **Strict data isolation** — Users can only access their own events
- **No fake data** — Zero fabricated vendors, ratings, or AI responses
- **Bounded retries** — Quota errors fail fast; only transient spikes retried
- **CORS restricted** — No wildcard origins with credentials

---

## 📜 Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | Google Gemini 3.8-Flash (with 2.5/3.5 fallback) |
| **Backend** | Python, FastAPI, Uvicorn |
| **Database** | SQLite (WAL mode) |
| **Vector DB** | ChromaDB (ephemeral, event-scoped RAG) |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (no frameworks) |
| **Auth** | HTTP-only SameSite cookies, `secrets.token_urlsafe(32)` |
| **Container** | Docker (Python 3.11-slim) |
| **Deployment** | Google Cloud Run |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

**Built for Prompt Wars 2026** ⚡
