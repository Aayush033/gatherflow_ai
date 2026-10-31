from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

# --- USER & AUTH SCHEMAS ---
class UserOut(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = "user"
    created_at: Optional[str] = None
    # Security requirement: session token is not exposed in API response body

class EvaluatorLoginRequest(BaseModel):
    passcode: Optional[str] = "gatherflow-evaluator"

# --- EVENT SCHEMAS ---
class EventBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150, description="Event title or celebration name")
    event_type: str = Field(..., description="wedding, birthday, community, or custom")
    date: str = Field(..., description="ISO Date string YYYY-MM-DD")
    time_details: Optional[str] = Field(None, max_length=100)
    location: str = Field(..., min_length=2, max_length=200)
    venue_preferences: Optional[str] = Field(None, max_length=300)
    guest_count: int = Field(..., gt=0, le=100000, description="Expected guest count")
    budget: float = Field(..., ge=0, description="Total planned budget")
    currency: str = Field(default="INR", max_length=10)
    theme: Optional[str] = Field(None, max_length=200)
    cultural_preferences: Optional[str] = Field(None, max_length=500)
    dietary_accessibility: Optional[str] = Field(None, max_length=500)
    priorities_constraints: Optional[str] = Field(None, max_length=500)

class EventCreate(EventBase):
    pass

class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[str] = None
    date: Optional[str] = None
    time_details: Optional[str] = None
    location: Optional[str] = None
    venue_preferences: Optional[str] = None
    guest_count: Optional[int] = None
    budget: Optional[float] = None
    currency: Optional[str] = None
    theme: Optional[str] = None
    cultural_preferences: Optional[str] = None
    dietary_accessibility: Optional[str] = None
    priorities_constraints: Optional[str] = None

class EventOut(EventBase):
    id: str
    user_id: str
    created_at: str
    updated_at: str
    plan_status: Optional[str] = "ready"
    plan_warning: Optional[str] = None

# --- EVENT PLAN SCHEMAS ---
class BudgetAllocationItem(BaseModel):
    category: str
    percentage: float
    estimated_amount: float
    description: Optional[str] = None

class TimelineMilestone(BaseModel):
    phase: str
    timeframe: str
    description: str

class ChecklistItem(BaseModel):
    task: str
    category: str
    priority: str = "medium"
    suggested_days_before: int = 14

class EventPlanData(BaseModel):
    concept: str
    theme_details: str
    budget_allocations: List[BudgetAllocationItem] = []
    timeline_milestones: List[TimelineMilestone] = []
    suggested_checklist: List[ChecklistItem] = []
    vendor_categories: List[str] = []
    risks: List[str] = []
    contingencies: List[str] = []
    next_actions: List[str] = []

class EventPlanOut(BaseModel):
    id: str
    event_id: str
    concept: Optional[str]
    theme_details: Optional[str]
    budget_allocation_json: Optional[str]
    timeline_milestones_json: Optional[str]
    checklist_json: Optional[str]
    vendor_categories_json: Optional[str]
    risks_json: Optional[str]
    contingencies_json: Optional[str]
    next_actions_json: Optional[str]
    is_ai_generated: bool
    created_at: str
    updated_at: str

class EventPlanUpdate(BaseModel):
    concept: Optional[str] = None
    theme_details: Optional[str] = None
    budget_allocation_json: Optional[str] = None
    timeline_milestones_json: Optional[str] = None
    checklist_json: Optional[str] = None

# --- BUDGET SCHEMAS ---
class BudgetItemBase(BaseModel):
    category: str = Field(..., min_length=2, max_length=80)
    item_name: str = Field(..., min_length=2, max_length=150)
    estimated_amount: float = Field(default=0.0, ge=0)
    quoted_amount: float = Field(default=0.0, ge=0)
    committed_amount: float = Field(default=0.0, ge=0)
    actual_amount: float = Field(default=0.0, ge=0)
    status: str = Field(default="planned") # planned, quoted, committed, paid
    notes: Optional[str] = None

class BudgetItemCreate(BudgetItemBase):
    pass

class BudgetItemUpdate(BaseModel):
    category: Optional[str] = None
    item_name: Optional[str] = None
    estimated_amount: Optional[float] = None
    quoted_amount: Optional[float] = None
    committed_amount: Optional[float] = None
    actual_amount: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class BudgetItemOut(BudgetItemBase):
    id: str
    event_id: str
    created_at: str
    updated_at: str

class CategoryBudgetBreakdown(BaseModel):
    category: str
    estimated_subtotal: float
    quoted_subtotal: float
    committed_subtotal: float
    actual_subtotal: float
    item_count: int

class BudgetSummaryOut(BaseModel):
    planned_budget: float
    total_estimated: float
    total_quoted: float
    total_committed: float
    total_actual: float
    remaining_from_committed: float
    remaining_from_actual: float
    currency: str
    is_over_budget: bool
    over_budget_amount: float
    alerts: List[str]
    categories: List[CategoryBudgetBreakdown]

class BudgetScenarioRequest(BaseModel):
    guest_count_delta: Optional[int] = 0
    budget_delta_percent: Optional[float] = 0.0 # e.g. -15.0 for 15% cut
    additional_expense: Optional[float] = 0.0
    notes: Optional[str] = None

class BudgetScenarioResponse(BaseModel):
    original_budget: float
    projected_budget: float
    original_guest_count: int
    projected_guest_count: int
    projected_cost_impact: float
    projected_variance: float
    is_feasible: bool
    deterministic_analysis: str
    ai_tradeoff_advice: Optional[str] = None

# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    category: str = Field(default="General", max_length=80)
    due_date: Optional[str] = None # YYYY-MM-DD
    priority: str = Field(default="medium") # low, medium, high, critical
    status: str = Field(default="todo") # todo, in_progress, completed
    assignee: Optional[str] = None
    dependency_task_id: Optional[str] = None
    notes: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None
    dependency_task_id: Optional[str] = None
    notes: Optional[str] = None

class TaskOut(TaskBase):
    id: str
    event_id: str
    is_overdue: bool = False
    days_remaining: Optional[int] = None
    created_at: str
    updated_at: str

class TaskSummaryOut(BaseModel):
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    todo_tasks: int
    overdue_tasks: int
    progress_percentage: float

# --- VENDOR SCHEMAS ---
class VendorBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    category: str = Field(..., min_length=2, max_length=80)
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    quotation_amount: float = Field(default=0.0, ge=0)
    status: str = Field(default="enquiry") # enquiry, shortlisted, quoted, confirmed, rejected
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    linked_budget_item_id: Optional[str] = None

class VendorCreate(VendorBase):
    pass

class VendorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    quotation_amount: Optional[float] = None
    status: Optional[str] = None
    follow_up_date: Optional[str] = None
    notes: Optional[str] = None
    linked_budget_item_id: Optional[str] = None

class VendorOut(VendorBase):
    id: str
    event_id: str
    created_at: str
    updated_at: str

# --- PLAN RESCUE SCHEMAS ---
class PlanRescueRequest(BaseModel):
    scenario_type: str = Field(..., description="budget_cut, guest_surge, vendor_cancelled, date_change, outdoor_weather, urgent_tasks, custom")
    description: str = Field(..., min_length=5, max_length=1000, description="Detailed situation description")
    target_budget: Optional[float] = None
    new_guest_count: Optional[int] = None
    new_date: Optional[str] = None

class PlanRescueProposedBudgetItem(BaseModel):
    category: str
    item_name: str
    current_estimate: float
    proposed_estimate: float
    adjustment_reason: str

class PlanRescueProposedTask(BaseModel):
    action: str # add, modify, delete
    title: str
    category: str
    priority: str
    due_date: Optional[str] = None
    notes: Optional[str] = None

class PlanRescueProposal(BaseModel):
    rescue_id: str
    situation_summary: str
    tradeoffs_and_impact: str
    confirmed_facts: List[str]
    ai_assumptions: List[str]
    proposed_event_updates: Optional[Dict[str, Any]] = None
    proposed_budget_adjustments: List[PlanRescueProposedBudgetItem] = []
    proposed_task_actions: List[PlanRescueProposedTask] = []
    immediate_actions: List[str] = []

class PlanRescueApplyRequest(BaseModel):
    rescue_id: str
    apply_event_updates: bool = True
    apply_budget_adjustments: bool = True
    apply_task_actions: bool = True

# --- COPILOT SCHEMAS ---
class CopilotMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

class CopilotResponse(BaseModel):
    reply: str
    suggested_actions: List[str] = []
    relevant_tab: Optional[str] = None # blueprint, budget, timeline, vendors, rescue

# --- EVENT BLUEPRINT FULL SUMMARY ---
class BlueprintHealthIndicators(BaseModel):
    has_overdue_tasks: bool
    overdue_task_count: int
    is_budget_critical: bool
    budget_usage_percent: float
    unconfirmed_critical_vendors: int
    days_to_event: int
    health_score: int # 0 to 100 objective composite score
    health_status: str # 'On Track', 'Needs Attention', 'Critical Action Required'
    alert_messages: List[str]

class NextBestAction(BaseModel):
    title: str
    description: str
    action_type: str # 'task', 'budget', 'vendor', 'plan_rescue', 'contingency'
    urgency: str # 'low', 'medium', 'high', 'critical'
    action_url: Optional[str] = None

class EventBlueprintOut(BaseModel):
    event: EventOut
    plan: Optional[EventPlanOut]
    budget_summary: BudgetSummaryOut
    task_summary: TaskSummaryOut
    health: BlueprintHealthIndicators
    next_best_action: NextBestAction
