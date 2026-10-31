"""
GatherFlow AI - Opt-in Live Gemini Verification Script
Executes a genuine model call against Google GenAI (gemini-3.8-flash)
when explicit server credentials (GEMINI_API_KEY) are provided.

Usage:
    python scripts/live_gemini_test.py
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.config import settings
from app.services.ai_service import get_genai_client, check_model_health, generate_initial_event_plan

def run_live_test():
    print("=" * 60, flush=True)
    print("GATHERFLOW AI — OPT-IN LIVE GEMINI 3.8 FLASH VERIFICATION", flush=True)
    print("=" * 60, flush=True)
    
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        print("[SKIPPED] GEMINI_API_KEY is not configured in .env or environment.", flush=True)
        print("To run live model tests, set GEMINI_API_KEY=<your_key> in .env", flush=True)
        return 0
        
    print(f"Target Model: {settings.GEMINI_MODEL}", flush=True)
    print(f"Key configured: {api_key[:6]}...{api_key[-4:]}", flush=True)
    print("\n1. Running Connectivity Smoke Test...", flush=True)
    
    health = check_model_health()
    print(f"Status: {health.get('status')}", flush=True)
    print(f"Connected: {health.get('connected')}", flush=True)
    print(f"Message: {health.get('message')}", flush=True)
    
    if not health.get("connected"):
        print("\n[RESULT] Live connectivity check did NOT confirm model access.", flush=True)
        return 1
        
    print("\n2. Testing Structured Event Planning Generation...", flush=True)
    sample_event = {
        "title": "Live Test Silver Anniversary Gala",
        "event_type": "wedding",
        "date": "2026-12-25",
        "location": "Udaipur, Rajasthan",
        "guest_count": 150,
        "budget": 800000.0,
        "currency": "INR",
        "theme": "Silver & Royal Blue Heritage",
        "cultural_preferences": "Vegetarian cuisine, classical sitar performance",
        "dietary_accessibility": "Wheelchair accessible banquet, nut-free dessert",
        "priorities_constraints": "Indoor contingency hall required"
    }
    
    try:
        plan = generate_initial_event_plan(sample_event)
        print("[SUCCESS] Model generated structured event plan:", flush=True)
        print(f"  Concept: {plan.concept[:120]}...", flush=True)
        print(f"  Budget Allocations ({len(plan.budget_allocations)} categories):", flush=True)
        for alloc in plan.budget_allocations[:3]:
            print(f"    - {alloc.category}: {alloc.percentage}% ({alloc.estimated_amount:,.2f} INR)", flush=True)
        print(f"  Milestones: {len(plan.timeline_milestones)}", flush=True)
        print(f"  Checklist Items: {len(plan.suggested_checklist)}", flush=True)
        print("\n[VERIFIED] Live Gemini 3.8 Flash model call completed and verified.", flush=True)
        return 0
    except Exception as e:
        print(f"[FAILED] Error generating live event plan: {e}", flush=True)
        return 1

if __name__ == "__main__":
    sys.exit(run_live_test())
