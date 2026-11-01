"""
GatherFlow AI - Pre-staged Demonstration Showcase Data
Provides structured template data for evaluators and judges to test
the entire application without burning external API quotas.
"""

import json
from datetime import date, timedelta
from typing import Any


def get_demo_event_payload(event_id: str, user_id: str, event_date: str) -> tuple[Any, ...]:
    return (
        event_id,
        user_id,
        "🌟 Global Tech & Innovation Gala 2026",
        "corporate",
        event_date,
        "18:00 - 23:30 (Keynote at 19:15, Banquet Dinner at 20:30)",
        "Metropolitan Convention Center — Grand Ballroom, Hall A",
        "Full A/V setup, motorized projection walls, dual catering prep kitchens",
        250,
        50000.0,
        "USD",
        "Modern Cyber Elegance & Luminescent Architecture",
        "International business formal, multilingual greeting materials",
        "35 Vegan/GF pre-registered; ADA compliant ramps to all stages",
        "Zero audiovisual latency, strict $50,000 budget cap, executive VIP lounge",
    )


def get_demo_plan_payload(plan_id: str, event_id: str) -> tuple[Any, ...]:
    budget_allocations = [
        {
            "category": "Venue",
            "percentage": 30.0,
            "estimated_amount": 15000.0,
            "description": "Grand ballroom & VIP green room rental",
        },
        {
            "category": "Catering",
            "percentage": 36.0,
            "estimated_amount": 18000.0,
            "description": "Executive 4-course dinner & open bar package",
        },
        {
            "category": "Audiovisual",
            "percentage": 17.0,
            "estimated_amount": 8500.0,
            "description": "Concert-grade sound & dual 4K LED walls",
        },
        {
            "category": "Entertainment",
            "percentage": 9.0,
            "estimated_amount": 4500.0,
            "description": "Keynote speaker honorarium & travel",
        },
        {
            "category": "Decor",
            "percentage": 8.0,
            "estimated_amount": 4000.0,
            "description": "Luminescent centerpieces & ambient uplighting",
        },
    ]

    milestones = [
        {
            "milestone": "Contracts & Venue Deposit Finalized",
            "target_days_before": 45,
            "description": "Lock space and liability insurance",
        },
        {
            "milestone": "Vendor Technical Rehearsal Lock",
            "target_days_before": 14,
            "description": "Final sound checks and culinary tastings",
        },
        {
            "milestone": "VIP Invitation Roster Confirmation",
            "target_days_before": 7,
            "description": "Seat assignments and dietary badges",
        },
        {
            "milestone": "Gala Day Execution & Live Stage Runs",
            "target_days_before": 0,
            "description": "On-site command center operations",
        },
    ]

    checklist = [
        {
            "task": "Execute Grand Ballroom Lease & Liability Insurance",
            "category": "Venue",
            "suggested_days_before": 35,
            "priority": "high",
        },
        {
            "task": "Approve Audio/Visual Rider & LED Wall Schematics",
            "category": "Audiovisual",
            "suggested_days_before": 20,
            "priority": "high",
        },
        {
            "task": "Complete VIP Catering Menu Tasting & Dietary List",
            "category": "Catering",
            "suggested_days_before": 18,
            "priority": "high",
        },
        {
            "task": "Send QR-Code Entry Passes to 250 Registered Guests",
            "category": "Logistics",
            "suggested_days_before": 10,
            "priority": "medium",
        },
        {
            "task": "Full Production Stage Rehearsal & Lighting Cues",
            "category": "Production",
            "suggested_days_before": 1,
            "priority": "high",
        },
        {
            "task": "Post-Gala Financial Reconciliation & Deposit Return",
            "category": "Finance",
            "suggested_days_before": -3,
            "priority": "low",
        },
    ]

    risks = [
        "High demand for A/V engineers during conference week",
        "Severe weather causing airport transit delays for VIP speakers",
        "Dietary overflow requiring on-demand kitchen adjustments",
    ]

    contingencies = [
        "Secondary A/V production team on 2-hour standby retainer",
        "Pre-arranged 10% banquet buffer with catering director",
        "Dual remote fiber link for live virtual keynote fallback",
    ]

    next_actions = [
        {
            "action": "Review signed technical rider with Apex AV Productions",
            "priority": "high",
            "timeline": "This week",
        },
        {
            "action": "Conduct final dietary count verification",
            "priority": "medium",
            "timeline": "Next week",
        },
    ]

    concept = (
        "A flagship corporate celebration blending executive networking, keynote thought leadership, "
        "and cinematic audiovisual immersion. Structured into three strategic phases: Welcome Cocktail "
        "Reception, Keynote & Awards, and Interactive Networking Gala."
    )
    theme = (
        "Deep obsidian and navy base accented by warm amber uplighting and frosted glass installations. "
        "Sustainable digital signage and branded interactive touchpoints throughout."
    )

    return (
        plan_id,
        event_id,
        concept,
        theme,
        json.dumps(budget_allocations),
        json.dumps(milestones),
        json.dumps(checklist),
        json.dumps(["Venue", "Catering", "Audiovisual", "Entertainment", "Decor"]),
        json.dumps(risks),
        json.dumps(contingencies),
        json.dumps(next_actions),
        0,  # is_ai_generated = 0: Accurately reflects pre-staged demonstration template
    )


def get_demo_budget_items(event_id: str, user_id: str) -> tuple[list[tuple[Any, ...]], str, str]:
    b_venue = f"bgt_demo_venue_{user_id[:6]}"
    b_cater = f"bgt_demo_cater_{user_id[:6]}"
    b_av = f"bgt_demo_av_{user_id[:6]}"
    b_keynote = f"bgt_demo_key_{user_id[:6]}"
    b_decor = f"bgt_demo_dec_{user_id[:6]}"

    rows = [
        (
            b_venue,
            event_id,
            "Venue",
            "Grand Ballroom & VIP Suite",
            15000.0,
            15000.0,
            15000.0,
            15000.0,
            "paid",
            "Fully settled. Security deposit refundable.",
        ),
        (
            b_cater,
            event_id,
            "Catering",
            "Executive 4-Course Banquet & Bar",
            18000.0,
            17500.0,
            0.0,
            0.0,
            "quoted",
            "Quote from Savor Gourmet Catering for 250 guests.",
        ),
        (
            b_av,
            event_id,
            "Audiovisual",
            "Concert Sound, Dual 4K LED Walls & Truss",
            8500.0,
            7800.0,
            7800.0,
            0.0,
            "committed",
            "Contract executed with Apex AV Productions.",
        ),
        (
            b_keynote,
            event_id,
            "Entertainment",
            "Keynote Speaker Honorarium & VIP Travel",
            4500.0,
            0.0,
            0.0,
            0.0,
            "planned",
            "Targeting industry keynote; legal agreement draft under review.",
        ),
        (
            b_decor,
            event_id,
            "Decor",
            "Luminescent Uplighting & Table Centerpieces",
            4000.0,
            3800.0,
            0.0,
            0.0,
            "quoted",
            "Includes setup and strike by 01:00.",
        ),
    ]
    return rows, b_av, b_cater


def get_demo_tasks(event_id: str, user_id: str, today: date) -> list[tuple[Any, ...]]:
    return [
        (
            f"tsk_demo_1_{user_id[:6]}",
            event_id,
            "Secure Grand Ballroom Lease & Liability Insurance",
            "Venue",
            (today + timedelta(days=10)).isoformat(),
            "high",
            "completed",
            "Executed and paid in full.",
        ),
        (
            f"tsk_demo_2_{user_id[:6]}",
            event_id,
            "Approve Audio/Visual Rider & LED Wall Schematics",
            "Audiovisual",
            (today + timedelta(days=25)).isoformat(),
            "high",
            "in_progress",
            "Marcus Vance coordinating crew schedule.",
        ),
        (
            f"tsk_demo_3_{user_id[:6]}",
            event_id,
            "Complete VIP Catering Menu Tasting & Dietary List",
            "Catering",
            (today + timedelta(days=27)).isoformat(),
            "high",
            "in_progress",
            "Chef Elena confirmed 35 vegan/GF courses.",
        ),
        (
            f"tsk_demo_4_{user_id[:6]}",
            event_id,
            "Send QR-Code Entry Passes to 250 Registered Guests",
            "Logistics",
            (today + timedelta(days=35)).isoformat(),
            "medium",
            "completed",
            "Automated digital invitations sent.",
        ),
        (
            f"tsk_demo_5_{user_id[:6]}",
            event_id,
            "Full Production Stage Rehearsal & Lighting Cues",
            "Production",
            (today + timedelta(days=44)).isoformat(),
            "high",
            "todo",
            "Scheduled for 16:00 day before event.",
        ),
        (
            f"tsk_demo_6_{user_id[:6]}",
            event_id,
            "Post-Gala Financial Reconciliation & Deposit Return",
            "Finance",
            (today + timedelta(days=48)).isoformat(),
            "low",
            "todo",
            "Review final supplier invoices against commitments.",
        ),
    ]


def get_demo_vendors(
    event_id: str, user_id: str, b_av_id: str, b_cater_id: str
) -> tuple[list[tuple[Any, ...]], list[dict[str, Any]]]:
    v_av_id = f"vnd_demo_av_{user_id[:6]}"
    v_cater_id = f"vnd_demo_cat_{user_id[:6]}"

    db_rows = [
        (
            v_av_id,
            event_id,
            "Apex Audiovisuals & Production",
            "Audiovisual",
            "Marcus Vance",
            "+1 (555) 234-5678",
            "marcus@apexav.example.com",
            7800.0,
            "confirmed",
            "Demonstration vendor profile. Includes 3 dedicated on-site sound engineers.",
            b_av_id,
        ),
        (
            v_cater_id,
            event_id,
            "Savor Gourmet Catering & Events",
            "Catering",
            "Elena Rostova",
            "+1 (555) 876-5432",
            "elena@savorcater.example.com",
            17500.0,
            "quoted",
            "Demonstration vendor profile. Full plated service + bar package for 250 attendees.",
            b_cater_id,
        ),
    ]

    vector_items = [
        {
            "id": v_av_id,
            "name": "Apex Audiovisuals & Production",
            "category": "Audiovisual",
            "quotation_amount": 7800.0,
            "notes": "Demonstration vendor profile. Includes 3 dedicated on-site sound engineers.",
        },
        {
            "id": v_cater_id,
            "name": "Savor Gourmet Catering & Events",
            "category": "Catering",
            "quotation_amount": 17500.0,
            "notes": "Demonstration vendor profile. Full plated service + bar package for 250 attendees.",
        },
    ]

    return db_rows, vector_items


def get_demo_rescue_log(rescue_id: str, event_id: str, today: date) -> tuple[Any, ...]:
    proposal = {
        "incident": "Lead Keynote Speaker canceled due to flight disruption 4 days before gala.",
        "impact_assessment": "High programmatic visibility impact. No financial penalty under agreement terms.",
        "recommended_strategy": "Activate local keynote speaker alternative; shift $1,000 speaker budget savings toward expedited rehearsal.",
        "budget_adjustments": [
            {
                "category": "Entertainment",
                "item_name": "Keynote Speaker (Local Alternative)",
                "amount_change": -1000.0,
                "rationale": "Local speaker honorarium is $3,500 vs $4,500 allocated (saves $1,000)",
            },
            {
                "category": "Audiovisual",
                "item_name": "Expedited Slide Rehearsal Support",
                "amount_change": 300.0,
                "rationale": "Extra 1-hr technician setup for slide reformatting",
            },
        ],
        "timeline_adjustments": [
            {
                "task": "Conduct Emergency Keynote Virtual Onboarding & Audio Check",
                "due_date": (today + timedelta(days=42)).isoformat(),
                "action": "add",
            }
        ],
        "guest_impact": "Zero disruption to gala schedule; attendees receive full keynote programming as planned.",
    }

    return (
        rescue_id,
        event_id,
        "Lead Keynote Speaker canceled due to flight disruption 4 days before gala.",
        "Activate local keynote speaker on alternative list; saves $1,000.",
        json.dumps(proposal),
    )
