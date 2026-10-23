"""Shared contract: Pydantic models for the DynamoDB records (§7) and API shapes (§8).

This is the one place P1, P2 and P3 agree on data shapes. The TypeScript
mirror is frontend/src/api/types.ts. Change both in the same PR.

Shapes the plan does not spell out are marked PROPOSED; confirm them at H0
(see docs/PROGRESS.md, Open questions).

Implements: PLAN.md §4 (Job 2 assessment), §5 (score breakdown, bands), §7, §8.
Owner: P2 (Backend and infra), reviewed by P1 and P3.
"""

from typing import Any, Literal

from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Enums (§3, §4, §5, §7)
# ---------------------------------------------------------------------------

Language = Literal["en", "es", "vi"]
Device = Literal["oxygen", "dialysis", "insulin", "power_wheelchair", "other"]
CaseStatus = Literal[
    "not_contacted",
    "awaiting_reply",
    "ok",
    "needs_help",
    "escalated",
    "silent",
    "dispatched",
    "resolved",
]
Band = Literal["Critical", "High", "Watch", "OK"]
AssessmentStatus = Literal["ok", "needs_help", "unclear"]
Need = Literal[
    "cooling_for_medication",
    "power_for_device",
    "transport",
    "medication_resupply",
    "welfare_check",
    "other",
]
EscalationLevel = Literal[0, 1, 2, 3]
Direction = Literal["out", "in"]
Channel = Literal["sms", "contact", "door"]
PlanStatus = Literal["draft", "approved"]
EventType = Literal[
    "outage_started",
    "checkins_sent",
    "reply",
    "escalation",
    "band_change",
    "plan_drafted",
    "plan_approved",
    "stop_done",
]
ResourceType = Literal["resource_center", "pharmacy"]
StopAction = Literal["cooler", "battery", "door_knock", "ride"]
BedrockJob = Literal["checkin", "assess", "explain", "escalate", "planner"]

# Timestamps are ISO 8601 strings in UTC (virtual time where noted).
Timestamp = str


class LatLng(BaseModel):
    lat: float
    lng: float


# ---------------------------------------------------------------------------
# Records (§7)
# ---------------------------------------------------------------------------


class EmergencyContact(BaseModel):
    name: str
    relation: str
    phone: str
    language: Language


class Resident(BaseModel):
    """Table `residents`, PK resident_id. Seeded from data/residents.json."""

    resident_id: str
    name: str
    age: int
    phone: str
    address: str
    lat: float
    lng: float
    language: Language
    devices: list[Device]
    baseline_backup_hours: float
    lives_alone: bool
    emergency_contact: EmergencyContact
    notes: str = ""


class Outage(BaseModel):
    """Table `outages`, PK outage_id."""

    outage_id: str
    name: str
    polygon: dict[str, Any]  # GeoJSON Polygon geometry
    starts_at: Timestamp
    est_restore_at: Timestamp
    affected_ids: list[str]
    status: str  # PROPOSED values: "active" | "restored"


class Assessment(BaseModel):
    """Job 2 forced tool call `record_assessment` (§4). Also the tool's input schema."""

    status: AssessmentStatus
    needs: list[Need]
    supply_hours_left: float | None
    needs_transport: bool
    distress_level: int  # 0-3
    detected_language: str
    english_translation: str
    key_quote: str  # verbatim, original language
    confidence: float  # 0-1; below 0.6 sets Case.needs_review
    reasoning: str  # 1-2 sentences


class ScoreBreakdown(BaseModel):
    """Deterministic triage score parts (§5). PROPOSED field names."""

    device_weight: float
    time_pressure: float
    alone: float
    silence: float
    distress: float
    transport: float
    status_ok_multiplier: float  # 1.0, or 0.2 when status is ok with confidence >= 0.8
    total: float


class Case(BaseModel):
    """Table `cases`, PK outage_id, SK resident_id."""

    outage_id: str
    resident_id: str
    status: CaseStatus
    priority: float
    band: Band
    score_breakdown: ScoreBreakdown | None = None
    rationale: str | None = None  # Job 3 one-line "why"
    assessment: Assessment | None = None
    escalation_level: EscalationLevel = 0
    last_outbound_at: Timestamp | None = None
    last_inbound_at: Timestamp | None = None
    needs_review: bool = False


class Message(BaseModel):
    """Table `messages`, PK resident_id, SK ts."""

    resident_id: str
    ts: Timestamp
    direction: Direction
    channel: Channel
    text: str
    translation_en: str | None = None
    image_key: str | None = None  # S3 key of a reply photo
    trace_id: str | None = None


class Stop(BaseModel):
    resident_id: str
    action: StopAction
    items: list[str]
    reason: str  # agent's one-line reason
    eta: Timestamp | None = None


class Run(BaseModel):
    run_id: str
    volunteer: str  # volunteer_id from data/volunteers.json
    vehicle: str
    stops: list[Stop]  # in visit order
    geometry: dict[str, Any] | None = None  # GeoJSON LineString from CalculateRoutes
    duration_min: float | None = None


class Plan(BaseModel):
    """Table `plans`, PK plan_id."""

    plan_id: str
    outage_id: str
    status: PlanStatus
    runs: list[Run]
    summary: str
    trace_id: str | None = None
    uncovered: list[str] = []  # open cases with priority >= 60 that didn't fit: "next wave"


class ToolCall(BaseModel):
    """One tool call inside a trace. PROPOSED shape."""

    name: str
    input: dict[str, Any]
    output: Any = None


class Trace(BaseModel):
    """Table `traces`, PK trace_id. One row per Bedrock call (§4)."""

    trace_id: str
    ts: Timestamp
    job: BedrockJob
    model_id: str
    input_masked: str
    tool_calls: list[ToolCall] = []
    output: Any = None
    latency_ms: int
    input_tokens: int
    output_tokens: int
    guardrail_action: str | None = None


class Event(BaseModel):
    """Table `events`, PK outage_id, SK ts. Feeds the timeline (§5)."""

    outage_id: str
    ts: Timestamp  # virtual time
    type: EventType
    label: str
    resident_id: str | None = None
    from_status: CaseStatus | None = None
    to_status: CaseStatus | None = None


class Volunteer(BaseModel):
    """Stored in `config` under key `volunteers`. Seeded from data/volunteers.json."""

    volunteer_id: str
    name: str
    phone: str
    vehicle: str
    start: LatLng
    capacity: int  # PROPOSED meaning: passenger seats for ride stops


class Resource(BaseModel):
    """Stored in `config` under key `resources`. Seeded from data/resources.json."""

    resource_id: str
    name: str
    type: ResourceType
    address: str
    lat: float
    lng: float
    offers: list[str] = []  # PROPOSED, e.g. "charging", "ice", "cooling"


# ---------------------------------------------------------------------------
# API requests and responses (§8)
# ---------------------------------------------------------------------------


class CreateOutageRequest(BaseModel):
    name: str
    polygon: dict[str, Any]
    starts_at: Timestamp
    est_restore_at: Timestamp


class CreateOutageResponse(BaseModel):
    outage_id: str
    affected: list[str]


class CheckinsResponse(BaseModel):
    sent: int


class InboundRequest(BaseModel):
    phone: str
    text: str
    image_b64: str | None = None  # resized client-side to under 1 MB (§16)


class CaseResponse(BaseModel):
    case: Case


class ClockAdvanceRequest(BaseModel):
    minutes: int


class Escalation(BaseModel):
    """One escalation step taken during /clock/advance. PROPOSED shape."""

    resident_id: str
    level: EscalationLevel
    channel: Channel
    text: str


class ClockAdvanceResponse(BaseModel):
    now: Timestamp
    escalations: list[Escalation]


class CreatePlanRequest(BaseModel):
    outage_id: str


class PlanResponse(BaseModel):
    plan: Plan


class Counts(BaseModel):
    safe: int
    needs_help: int
    critical: int
    no_reply: int


class DashboardCase(Case):
    """A case as /dashboard returns it. PROPOSED: embeds the resident so the
    map can place markers without a second call."""

    resident: Resident
    backup_hours_left: float | None  # at virtual now


class DashboardResponse(BaseModel):
    now: Timestamp
    outage: Outage | None
    counts: Counts
    cases: list[DashboardCase]
    events: list[Event]
    plan: Plan | None = None
    resources: list[Resource]
    volunteers: list[Volunteer]


class MessagesResponse(BaseModel):
    messages: list[Message]


class TracesResponse(BaseModel):
    traces: list[Trace]


class RunResponse(BaseModel):
    run: Run
