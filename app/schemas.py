from typing import Any

from pydantic import BaseModel, Field


# --- USER & AUTH SCHEMAS ---
class UserOut(BaseModel):
    id: str
    email: str | None = None
    name: str | None = None
    role: str | None = "user"
    created_at: str | None = None
    # Security requirement: session token is not exposed in API response body


class EvaluatorLoginRequest(BaseModel):
    passcode: str | None = "gatherflow-evaluator"


# --- EVENT SCHEMAS ---
class EventBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150, description="Event title or celebration name")
    event_type: str = Field(..., description="wedding, birthday, community, or custom")
    date: str = Field(..., description="ISO Date string YYYY-MM-DD")
    time_details: str | None = Field(None, max_length=100)
    location: str = Field(..., min_length=2, max_length=200)
    venue_preferences: str | None = Field(None, max_length=300)
    guest_count: int = Field(..., gt=0, le=100000, description="Expected guest count")
    budget: float = Field(..., ge=0, description="Total planned budget")
    currency: str = Field(default="INR", max_length=10)
    theme: str | None = Field(None, max_length=200)
    cultural_preferences: str | None = Field(None, max_length=500)
    dietary_accessibility: str | None = Field(None, max_length=500)
    priorities_constraints: str | None = Field(None, max_length=500)


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: str | None = None
    event_type: str | None = None
    date: str | None = None
    time_details: str | None = None
    location: str | None = None
    venue_preferences: str | None = None
    guest_count: int | None = None
    budget: float | None = None
    currency: str | None = None
    theme: str | None = None
    cultural_preferences: str | None = None
    dietary_accessibility: str | None = None
    priorities_constraints: str | None = None


class EventOut(EventBase):
    id: str
    user_id: str
    created_at: str
    updated_at: str
    plan_status: str | None = "ready"
    plan_warning: str | None = None


# --- EVENT PLAN SCHEMAS ---
class BudgetAllocationItem(BaseModel):
    category: str
    percentage: float
    estimated_amount: float
    description: str | None = None


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
    budget_allocations: list[BudgetAllocationItem] = []
    timeline_milestones: list[TimelineMilestone] = []
    suggested_checklist: list[ChecklistItem] = []
    vendor_categories: list[str] = []
    risks: list[str] = []
    contingencies: list[str] = []
    next_actions: list[str] = []


class EventPlanOut(BaseModel):
    id: str
    event_id: str
    concept: str | None
    theme_details: str | None
    budget_allocation_json: str | None
    timeline_milestones_json: str | None
    checklist_json: str | None
    vendor_categories_json: str | None
    risks_json: str | None
    contingencies_json: str | None
    next_actions_json: str | None
    is_ai_generated: bool
    created_at: str
    updated_at: str


class EventPlanUpdate(BaseModel):
    concept: str | None = None
    theme_details: str | None = None
    budget_allocation_json: str | None = None
    timeline_milestones_json: str | None = None
    checklist_json: str | None = None


# --- BUDGET SCHEMAS ---
class BudgetItemBase(BaseModel):
    category: str = Field(..., min_length=2, max_length=80)
    item_name: str = Field(..., min_length=2, max_length=150)
    estimated_amount: float = Field(default=0.0, ge=0)
    quoted_amount: float = Field(default=0.0, ge=0)
    committed_amount: float = Field(default=0.0, ge=0)
    actual_amount: float = Field(default=0.0, ge=0)
    status: str = Field(default="planned")  # planned, quoted, committed, paid
    notes: str | None = None


class BudgetItemCreate(BudgetItemBase):
    pass


class BudgetItemUpdate(BaseModel):
    category: str | None = None
    item_name: str | None = None
    estimated_amount: float | None = None
    quoted_amount: float | None = None
    committed_amount: float | None = None
    actual_amount: float | None = None
    status: str | None = None
    notes: str | None = None


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
    alerts: list[str]
    categories: list[CategoryBudgetBreakdown]


class BudgetScenarioRequest(BaseModel):
    guest_count_delta: int | None = 0
    budget_delta_percent: float | None = 0.0  # e.g. -15.0 for 15% cut
    additional_expense: float | None = 0.0
    notes: str | None = None


class BudgetScenarioResponse(BaseModel):
    original_budget: float
    projected_budget: float
    original_guest_count: int
    projected_guest_count: int
    projected_cost_impact: float
    projected_variance: float
    is_feasible: bool
    deterministic_analysis: str
    ai_tradeoff_advice: str | None = None


# --- TASK SCHEMAS ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str | None = None
    category: str = Field(default="General", max_length=80)
    due_date: str | None = None  # YYYY-MM-DD
    priority: str = Field(default="medium")  # low, medium, high, critical
    status: str = Field(default="todo")  # todo, in_progress, completed
    assignee: str | None = None
    dependency_task_id: str | None = None
    notes: str | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    due_date: str | None = None
    priority: str | None = None
    status: str | None = None
    assignee: str | None = None
    dependency_task_id: str | None = None
    notes: str | None = None


class TaskOut(TaskBase):
    id: str
    event_id: str
    is_overdue: bool = False
    days_remaining: int | None = None
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
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    quotation_amount: float = Field(default=0.0, ge=0)
    status: str = Field(default="enquiry")  # enquiry, shortlisted, quoted, confirmed, rejected
    follow_up_date: str | None = None
    notes: str | None = None
    linked_budget_item_id: str | None = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    contact_person: str | None = None
    contact_phone: str | None = None
    contact_email: str | None = None
    quotation_amount: float | None = None
    status: str | None = None
    follow_up_date: str | None = None
    notes: str | None = None
    linked_budget_item_id: str | None = None


class VendorOut(VendorBase):
    id: str
    event_id: str
    created_at: str
    updated_at: str


# --- PLAN RESCUE SCHEMAS ---
class PlanRescueRequest(BaseModel):
    scenario_type: str = Field(
        ..., description="budget_cut, guest_surge, vendor_cancelled, date_change, outdoor_weather, urgent_tasks, custom"
    )
    description: str = Field(..., min_length=5, max_length=1000, description="Detailed situation description")
    target_budget: float | None = None
    new_guest_count: int | None = None
    new_date: str | None = None


class PlanRescueProposedBudgetItem(BaseModel):
    category: str
    item_name: str
    current_estimate: float
    proposed_estimate: float
    adjustment_reason: str


class PlanRescueProposedTask(BaseModel):
    action: str  # add, modify, delete
    title: str
    category: str
    priority: str
    due_date: str | None = None
    notes: str | None = None


class PlanRescueProposal(BaseModel):
    rescue_id: str
    situation_summary: str
    tradeoffs_and_impact: str
    confirmed_facts: list[str]
    ai_assumptions: list[str]
    proposed_event_updates: dict[str, Any] | None = None
    proposed_budget_adjustments: list[PlanRescueProposedBudgetItem] = []
    proposed_task_actions: list[PlanRescueProposedTask] = []
    immediate_actions: list[str] = []


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
    suggested_actions: list[str] = []
    relevant_tab: str | None = None  # blueprint, budget, timeline, vendors, rescue


# --- EVENT BLUEPRINT FULL SUMMARY ---
class BlueprintHealthIndicators(BaseModel):
    has_overdue_tasks: bool
    overdue_task_count: int
    is_budget_critical: bool
    budget_usage_percent: float
    unconfirmed_critical_vendors: int
    days_to_event: int
    health_score: int  # 0 to 100 objective composite score
    health_status: str  # 'On Track', 'Needs Attention', 'Critical Action Required'
    alert_messages: list[str]


class NextBestAction(BaseModel):
    title: str
    description: str
    action_type: str  # 'task', 'budget', 'vendor', 'plan_rescue', 'contingency'
    urgency: str  # 'low', 'medium', 'high', 'critical'
    action_url: str | None = None


class EventBlueprintOut(BaseModel):
    event: EventOut
    plan: EventPlanOut | None
    budget_summary: BudgetSummaryOut
    task_summary: TaskSummaryOut
    health: BlueprintHealthIndicators
    next_best_action: NextBestAction
