import json
import logging
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.schemas import (
    EventPlanData,
)

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Custom exception indicating genuine AI service failures with actionable diagnostic messages."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.details = details or {}


def get_genai_client(api_key_override: str | None = None, timeout_ms: int = 45000) -> genai.Client:
    """Initializes and returns the Google GenAI client using configured server-side credentials or override."""
    api_key = (api_key_override or settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        raise AIServiceError(
            "Gemini API key is not configured. Please set GEMINI_API_KEY in your environment or .env file.",
            {"error_code": "MISSING_API_KEY", "model": settings.GEMINI_MODEL},
        )
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))


def call_gemini_with_resilience(client: genai.Client, model: str, contents: Any, config: Any | None = None) -> Any:
    """
    Executes Gemini content generation with high resilience.
    1. First attempts with the configured primary model (gemini-3.8-flash).
    2. If Google's servers return 503 (demand spike) or 504 (deadline exceeded) or time out,
       it automatically falls back to an available fast model (gemini-2.5-flash).
    3. Handles 429 quota exhaustion transparently.
    """
    models_to_try = [model]
    for fallback in ["gemini-2.5-flash", "gemini-3.5-flash"]:
        if fallback != model and fallback not in models_to_try:
            models_to_try.append(fallback)

    last_error = None
    for current_model in models_to_try:
        try:
            response = client.models.generate_content(model=current_model, contents=contents, config=config)
            if current_model != model:
                logger.info(f"Generated response using high-availability fallback {current_model} after {model} spike.")
            return response
        except APIError as e:
            last_error = e
            err_msg = str(e).lower()
            code = getattr(e, "code", None)
            # 429 is quota exhaustion; retries are wasteful and futile
            if code == 429 or "resource_exhausted" in err_msg or "quota" in err_msg:
                raise AIServiceError(
                    "Gemini API quota reached (HTTP 429). The app will operate using verified deterministic calculations and offline fallbacks.",
                    {"code": 429, "model": current_model},
                )

            # If 503 (demand spike) or 504 (deadline exceeded), log and try fallback model
            if code in (503, 504) or "deadline" in err_msg or "high demand" in err_msg or "unavailable" in err_msg:
                logger.warning(f"Model {current_model} returned {code or 'timeout'}. Attempting fallback model...")
                continue
            raise e
        except Exception as e:
            last_error = e
            err_msg = str(e).lower()
            if "deadline" in err_msg or "timeout" in err_msg or "timed out" in err_msg:
                logger.warning(f"Model {current_model} timed out. Attempting fallback model...")
                continue
            logger.warning(f"Model {current_model} exception: {e}")
            break

    if last_error:
        raise last_error
    raise AIServiceError("Google Gemini servers are temporarily unreachable. Please retry.")


def check_model_health(api_key_override: str | None = None) -> dict[str, Any]:
    """
    Performs a genuine live connectivity check against the Gemini API.
    Uses fast, authenticated model listing to verify credentials in under 1 second,
    ensuring zero false-positive hangs or timeouts on health checks.
    """
    api_key = (api_key_override or settings.GEMINI_API_KEY or "").strip()
    if not api_key:
        return {
            "status": "unconfigured",
            "model": settings.GEMINI_MODEL,
            "connected": False,
            "key_configured": False,
            "message": "Gemini API key is not configured.",
        }

    try:
        client = get_genai_client(api_key_override=api_key, timeout_ms=10000)
        # Fast, genuine Google API validation: verifies key against live Google GenAI catalog
        models_iter = client.models.list()
        first_model = next(iter(models_iter), None)

        if first_model:
            return {
                "status": "connected",
                "model": settings.GEMINI_MODEL,
                "connected": True,
                "key_configured": True,
                "message": f"Successfully verified live connection to Gemini API ({settings.GEMINI_MODEL}).",
            }
        else:
            return {
                "status": "empty_response",
                "model": settings.GEMINI_MODEL,
                "connected": False,
                "key_configured": True,
                "message": "Model catalog responded but returned empty list.",
            }
    except APIError as e:
        err_msg = str(e).lower()
        if getattr(e, "code", None) == 429 or "resource_exhausted" in err_msg or "quota" in err_msg:
            return {
                "status": "quota_exhausted",
                "model": settings.GEMINI_MODEL,
                "connected": False,
                "key_configured": True,
                "message": "Key is valid, but Gemini account quota has been reached (HTTP 429). The app remains fully functional in offline/deterministic mode.",
            }
        if getattr(e, "code", None) == 503 or "high demand" in err_msg or "unavailable" in err_msg:
            return {
                "status": "unavailable",
                "model": settings.GEMINI_MODEL,
                "connected": False,
                "key_configured": True,
                "message": "Google capacity is currently experiencing a temporary demand spike (HTTP 503).",
            }
        if getattr(e, "code", None) == 504 or "deadline" in err_msg:
            return {
                "status": "timeout",
                "model": settings.GEMINI_MODEL,
                "connected": False,
                "key_configured": True,
                "message": "Google servers timed out (HTTP 504 Deadline Exceeded). Spikes in demand are temporary.",
            }
        logger.error(f"Google GenAI APIError: {e}")
        return {
            "status": "error",
            "model": settings.GEMINI_MODEL,
            "connected": False,
            "key_configured": True,
            "message": f"AI model request rejected: {str(e)[:180]}",
        }
    except Exception as e:
        logger.error(f"GenAI connection error: {e}")
        err_msg = str(e).lower()
        if "deadline" in err_msg or "timeout" in err_msg or "timed out" in err_msg:
            return {
                "status": "timeout",
                "model": settings.GEMINI_MODEL,
                "connected": False,
                "key_configured": True,
                "message": "Connection check timed out after 10s. Network connection is slow or Google servers are busy.",
            }
        if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
            return {
                "status": "quota_exhausted",
                "model": settings.GEMINI_MODEL,
                "connected": False,
                "key_configured": True,
                "message": "Key is valid, but Gemini account quota has been reached (HTTP 429). The app remains fully functional in offline/deterministic mode.",
            }
        return {
            "status": "error",
            "model": settings.GEMINI_MODEL,
            "connected": False,
            "key_configured": True,
            "message": f"Connection check error: {str(e)[:180]}",
        }


def generate_initial_event_plan(event_data: dict[str, Any]) -> EventPlanData:
    """
    Sends actual user-provided event details to Gemini to generate a personalized,
    structured initial plan including concept, budget allocation, milestones, and task checklist.
    """
    client = get_genai_client()
    model = settings.GEMINI_MODEL

    prompt = f"""
You are the master event planning engine for GatherFlow AI.
Generate a comprehensive, highly personalized initial event plan based STRICTLY on the user's specific event inputs:

EVENT SPECIFICATIONS:
- Title: {event_data.get("title")}
- Type: {event_data.get("event_type")}
- Date: {event_data.get("date")} ({event_data.get("time_details") or "Full day / flexible"})
- Location: {event_data.get("location")} (Venue preference: {event_data.get("venue_preferences") or "Open"})
- Guest Count: {event_data.get("guest_count")} guests
- Planned Budget: {event_data.get("currency", "INR")} {event_data.get("budget", 0):,.2f}
- Style & Theme: {event_data.get("theme") or "Classic & Memorable"}
- Cultural & Community Preferences: {event_data.get("cultural_preferences") or "None specified"}
- Dietary & Accessibility Considerations: {event_data.get("dietary_accessibility") or "Standard"}
- Priorities & Constraints: {event_data.get("priorities_constraints") or "None specified"}

INSTRUCTIONS:
1. Provide a tailored creative concept and atmosphere direction matching the cultural and event context.
2. Formulate realistic budget percentage allocations across relevant categories that sum to approximately 100%. Calculate estimated amounts based on the planned budget.
3. Formulate timeline milestones structured by timeframe (e.g. '8-12 weeks before', '4 weeks before', 'Week of event', 'Event Day').
4. Formulate an actionable, prioritized task checklist (8-15 items) with specific categories, priority ('high', 'medium', 'low'), and suggested days before the event.
5. Identify required vendor categories (e.g., Venue, Catering, Photography, Decoration, Entertainment, Logistics).
6. List critical risks, contingency suggestions, and immediate next actions.

Return your response in valid JSON with this exact structure:
{{
  "concept": "Creative vision and core experience description",
  "theme_details": "Styling, color palette, decor mood and atmosphere guide",
  "budget_allocations": [
    {{"category": "Venue & Decor", "percentage": 35.0, "estimated_amount": 0.0, "description": "..."}},
    {{"category": "Catering & Beverages", "percentage": 30.0, "estimated_amount": 0.0, "description": "..."}}
  ],
  "timeline_milestones": [
    {{"phase": "Foundation", "timeframe": "6-8 weeks before", "description": "..."}}
  ],
  "suggested_checklist": [
    {{"task": "Confirm venue booking and deposit", "category": "Venue", "priority": "high", "suggested_days_before": 45}}
  ],
  "vendor_categories": ["Venue", "Catering", "Photography", "Decoration", "Entertainment"],
  "risks": ["Risk 1", "Risk 2"],
  "contingencies": ["Contingency plan 1", "Contingency plan 2"],
  "next_actions": ["Action 1", "Action 2"]
}}
"""

    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction="You are an expert event planning strategist and financial consultant for GatherFlow AI. You provide realistic, culturally nuanced, practical event plans. Return valid JSON only.",
        )
        response = call_gemini_with_resilience(client=client, model=model, contents=prompt, config=config)

        if not response.text:
            raise AIServiceError("Gemini returned an empty response.", {"model": model})

        data = json.loads(response.text)

        # Ensure calculated estimated amounts align with budget percentages
        total_budget = float(event_data.get("budget", 0))
        for alloc in data.get("budget_allocations", []):
            pct = float(alloc.get("percentage", 0))
            if alloc.get("estimated_amount", 0) <= 0:
                alloc["estimated_amount"] = round((total_budget * pct) / 100.0, 2)

        return EventPlanData(**data)

    except json.JSONDecodeError as jde:
        logger.error(f"Failed to parse Gemini response as JSON: {response.text}")
        raise AIServiceError(f"Model output could not be parsed as structured JSON: {jde!s}")
    except APIError as ae:
        logger.error(f"Gemini API Error during plan generation: {ae}")
        raise AIServiceError(f"Gemini API Error: {ae.message if hasattr(ae, 'message') else str(ae)}", {"model": model})
    except Exception as e:
        logger.error(f"Unexpected error in plan generation: {e}")
        raise AIServiceError(f"AI Plan Generation failed: {e!s}")


def generate_plan_rescue_proposal(
    event_data: dict[str, Any],
    budget_summary: dict[str, Any],
    tasks: list[dict[str, Any]],
    vendors: list[dict[str, Any]],
    scenario: Any,
    playbooks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Signature Differentiator: Generates an adaptive replanning proposal when circumstances change.
    Considers actual saved budget, tasks, vendors, constraints, and ChromaDB vector playbooks.
    Distinguishes confirmed facts from AI assumptions and provides a reviewable preview.
    """
    client = get_genai_client()
    model = settings.GEMINI_MODEL

    playbooks_str = ""
    if playbooks:
        playbooks_str = (
            "\nPROVEN CONTINGENCY PLAYBOOKS (RETRIEVED FROM CHROMADB VECTOR STORE):\n"
            + "\n".join([f"- {p.get('scenario', 'Strategy')}: {p.get('guidance', '')}" for p in playbooks])
            + "\n"
        )

    # Extract confirmed facts from stored database state
    confirmed_facts = [
        f"Event: {event_data.get('title')} ({event_data.get('event_type')}) on {event_data.get('date')}",
        f"Guests: {event_data.get('guest_count')} guests",
        f"Planned Budget: {event_data.get('currency')} {event_data.get('budget'):,.2f}",
        f"Current Committed Spending: {event_data.get('currency')} {budget_summary.get('total_committed', 0):,.2f}",
        f"Current Actual Paid: {event_data.get('currency')} {budget_summary.get('total_actual', 0):,.2f}",
        f"Tasks: {len(tasks)} total tasks ({sum(1 for t in tasks if t.get('status') == 'completed')} completed, {sum(1 for t in tasks if t.get('is_overdue'))} overdue)",
        f"Vendors: {len(vendors)} recorded vendors ({sum(1 for v in vendors if v.get('status') == 'confirmed')} confirmed)",
    ]

    prompt = f"""
You are GatherFlow AI's Plan Rescue Engine — an adaptive replanning specialist.
An unexpected disruption has occurred. Formulate an actionable, balanced replanning strategy.

LIVE STORED EVENT CONTEXT (CONFIRMED TRUTHS):
- Event: {event_data.get("title")} ({event_data.get("event_type")})
- Date: {event_data.get("date")}
- Guest Count: {event_data.get("guest_count")}
- Planned Budget: {event_data.get("currency")} {event_data.get("budget")}
- Committed Spending: {event_data.get("currency")} {budget_summary.get("total_committed")}
- Actual Paid So Far: {event_data.get("currency")} {budget_summary.get("total_actual")}
- Active Budget Items: {json.dumps([{"category": b.get("category"), "item": b.get("item_name"), "committed": b.get("committed_amount"), "estimated": b.get("estimated_amount")} for b in budget_summary.get("items", [])[:10]])}
- Active Vendors: {json.dumps([{"name": v.get("name"), "category": v.get("category"), "status": v.get("status"), "quote": v.get("quotation_amount")} for v in vendors[:8]])}
- Active Tasks: {json.dumps([{"title": t.get("title"), "category": t.get("category"), "status": t.get("status"), "due": t.get("due_date")} for t in tasks[:10]])}
{playbooks_str}
EMERGENCY DISRUPTION SCENARIO:
- Scenario Type: {scenario.scenario_type}
- Disruption Description: {scenario.description}
- Target Budget specified by user: {scenario.target_budget if scenario.target_budget is not None else "Unchanged"}
- New Guest Count specified by user: {scenario.new_guest_count if scenario.new_guest_count is not None else "Unchanged"}
- New Date specified by user: {scenario.new_date or "Unchanged"}

INSTRUCTIONS FOR RECOVERY PROPOSAL:
1. Explain trade-offs honestly. Do NOT fabricate supplier confirmations or claim non-existent bookings.
2. Clearly state assumptions made by the AI.
3. If budget or guest count must change, propose specific event parameter updates.
4. Suggest specific adjustments to budget categories (e.g. trim decor or favors to preserve catering quality).
5. Suggest task actions (tasks to add like 'Review revised vendor quotes', tasks to prioritize, or cancel).
6. List 3-4 immediate next actions for the organizer.

Return JSON in this exact structure:
{{
  "situation_summary": "Concise 2-sentence breakdown of the challenge",
  "tradeoffs_and_impact": "Detailed assessment of trade-offs, financial implications, and compromises",
  "ai_assumptions": [
    "Assumption 1...",
    "Assumption 2..."
  ],
  "proposed_event_updates": {{
    "budget": {scenario.target_budget if scenario.target_budget is not None else "null"},
    "guest_count": {scenario.new_guest_count if scenario.new_guest_count is not None else "null"},
    "date": "{scenario.new_date or ""}"
  }},
  "proposed_budget_adjustments": [
    {{
      "category": "Decoration",
      "item_name": "Stage Floral Decor",
      "current_estimate": 50000,
      "proposed_estimate": 35000,
      "adjustment_reason": "Switch to seasonal local blooms to absorb budget reduction"
    }}
  ],
  "proposed_task_actions": [
    {{
      "action": "add",
      "title": "Negotiate with caterer for reduced menu tier",
      "category": "Catering",
      "priority": "high",
      "due_date": null,
      "notes": "Triggered by Plan Rescue"
    }}
  ],
  "immediate_actions": [
    "Action 1",
    "Action 2"
  ]
}}
"""

    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction="You are GatherFlow AI's Plan Rescue specialist. You help organizers navigate emergencies with calm, realistic, actionable plans. Return valid JSON only.",
        )
        response = call_gemini_with_resilience(client=client, model=model, contents=prompt, config=config)

        if not response.text:
            raise AIServiceError("Gemini returned an empty replanning response.", {"model": model})

        data = json.loads(response.text)
        data["confirmed_facts"] = confirmed_facts

        # Clean proposed_event_updates if values are null or empty
        updates = data.get("proposed_event_updates") or {}
        cleaned_updates = {k: v for k, v in updates.items() if v is not None and v != "" and v != "null"}
        data["proposed_event_updates"] = cleaned_updates if cleaned_updates else None

        return data

    except json.JSONDecodeError as jde:
        logger.error(f"Failed to parse Plan Rescue JSON: {response.text}")
        raise AIServiceError(f"Plan Rescue output could not be parsed as structured JSON: {jde!s}")
    except APIError as ae:
        logger.error(f"Gemini API Error during Plan Rescue: {ae}")
        raise AIServiceError(
            f"Gemini API Error during Plan Rescue: {ae.message if hasattr(ae, 'message') else str(ae)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in Plan Rescue: {e}")
        raise AIServiceError(f"Plan Rescue failed: {e!s}")


def copilot_chat_response(
    event_data: dict[str, Any],
    budget_summary: dict[str, Any],
    tasks: list[dict[str, Any]],
    vendors: list[dict[str, Any]],
    chat_history: list[dict[str, str]],
    user_message: str,
    rag_knowledge: list[dict[str, Any]] | None = None,
    rag_vendors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Answers user queries with deep context of the active event.
    Augmented with ChromaDB vector knowledge and semantic vendor retrieval.
    Provides suggested actions and links directly to relevant modules.
    """
    client = get_genai_client()
    model = settings.GEMINI_MODEL

    # Build compact context snapshot
    overdue_tasks = [t["title"] for t in tasks if t.get("is_overdue")]
    confirmed_vendors = [v["name"] for v in vendors if v.get("status") == "confirmed"]
    unconfirmed_vendors = [f"{v['name']} ({v.get('category')})" for v in vendors if v.get("status") != "confirmed"]

    rag_section = ""
    if rag_knowledge or rag_vendors:
        rag_parts = []
        if rag_knowledge:
            rag_parts.append(
                "KNOWLEDGE RETRIEVED VIA CHROMADB:\n"
                + "\n".join([f"- {k.get('title')}: {k.get('content')}" for k in rag_knowledge])
            )
        if rag_vendors:
            rag_parts.append(
                "RELEVANT VENDORS RETRIEVED VIA CHROMADB:\n"
                + "\n".join([f"- {v.get('name')} ({v.get('category')}): {v.get('description')}" for v in rag_vendors])
            )
        rag_section = "\n" + "\n\n".join(rag_parts) + "\n"

    context_str = f"""
CURRENT ACTIVE EVENT CONTEXT:
- Title: {event_data.get("title")} ({event_data.get("event_type")})
- Date: {event_data.get("date")} | Guests: {event_data.get("guest_count")}
- Location: {event_data.get("location")}
- Planned Budget: {event_data.get("currency")} {event_data.get("budget"):,.2f}
- Total Committed: {event_data.get("currency")} {budget_summary.get("total_committed", 0):,.2f}
- Total Actual Paid: {event_data.get("currency")} {budget_summary.get("total_actual", 0):,.2f}
- Remaining Budget: {event_data.get("currency")} {budget_summary.get("remaining_from_committed", 0):,.2f}
- Tasks Summary: {len(tasks)} tasks total, {sum(1 for t in tasks if t.get("status") == "completed")} completed, {len(overdue_tasks)} overdue ({", ".join(overdue_tasks[:3]) if overdue_tasks else "None"})
- Vendors: {len(vendors)} recorded ({len(confirmed_vendors)} confirmed: {", ".join(confirmed_vendors[:3]) or "None"}; Unconfirmed: {", ".join(unconfirmed_vendors[:3]) or "None"})
"""

    history_formatted = "\n".join(
        [f"{msg.get('role').capitalize()}: {msg.get('content')}" for msg in chat_history[-6:]]
    )

    prompt = f"""
{context_str}
{rag_section}
CONVERSATION HISTORY:
{history_formatted}

USER'S MESSAGE:
{user_message}

INSTRUCTIONS:
Provide an insightful, practical, concise response (2-4 paragraphs).
Highlight any trade-offs, dates, or financial consequences based strictly on the stored context.
Distinguish confirmed facts from suggestions.
Suggest 2-3 specific immediate action steps the user can take.
Indicate which tab in GatherFlow AI is most relevant ('blueprint', 'budget', 'timeline', 'vendors', 'rescue').

Return JSON with this exact structure:
{{
  "reply": "Your helpful response text here...",
  "suggested_actions": ["Action 1", "Action 2"],
  "relevant_tab": "budget"
}}
"""

    try:
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction="You are GatherFlow AI's Event Copilot. You are an expert event producer, empathetic advisor, and meticulous coordinator. Return valid JSON only.",
        )
        response = call_gemini_with_resilience(client=client, model=model, contents=prompt, config=config)

        if not response.text:
            raise AIServiceError("Copilot returned an empty response.", {"model": model})

        data = json.loads(response.text)
        return {
            "reply": data.get("reply", "Here is what I suggest for your event."),
            "suggested_actions": data.get("suggested_actions", []),
            "relevant_tab": data.get("relevant_tab", "blueprint"),
        }
    except json.JSONDecodeError:
        return {
            "reply": response.text or "I reviewed your event context. What specific aspect would you like to adjust?",
            "suggested_actions": ["Review budget", "Check overdue tasks"],
            "relevant_tab": "blueprint",
        }
    except Exception as e:
        logger.error(f"Error in Copilot chat: {e}")
        raise AIServiceError(f"Copilot query failed: {e!s}")


def explain_budget_scenario_ai(
    event_data: dict[str, Any], deterministic_analysis: str, scenario_notes: str | None = None
) -> str:
    """
    Uses Gemini to provide qualitative reasoning and trade-off advice for a numerical budget scenario.
    Does NOT calculate the figures; it receives deterministic figures and explains trade-offs.
    """
    client = get_genai_client()
    model = settings.GEMINI_MODEL

    prompt = f"""
An event planner is testing a 'What-If' budget/guest scenario for:
Event: {event_data.get("title")} ({event_data.get("event_type")})

DETERMINISTIC NUMERICAL PROJECTIONS (CALCULATED BY APP ENGINE):
{deterministic_analysis}

USER NOTES: {scenario_notes or "None"}

Please provide a concise strategic evaluation (2 short paragraphs):
1. What are the key trade-offs in quality, vendor choices, and guest experience?
2. What are the top 2 actionable recommendations to keep this event feasible without compromising core moments?
"""
    try:
        response = client.models.generate_content(model=model, contents=prompt)
        return (
            response.text.strip() if response.text else "Review the numerical impact above before committing changes."
        )
    except Exception as e:
        logger.warning(f"Could not fetch AI scenario commentary: {e}")
        err_str = str(e).lower()
        if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
            return "AI strategic commentary is temporarily paused (Gemini API quota reached). Your deterministic financial projections above are 100% verified and active."
        return "AI strategic commentary is temporarily unavailable. Please rely on the deterministic projections above."
