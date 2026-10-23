"""FastAPI routes for every endpoint in the API contract, plus the Lambda handler.

Routes stay thin: they call store, triage, escalation, geo, location and the
Bedrock jobs. Request and response shapes come from schemas.py.

Implements: PLAN.md §8 (API contract), §6 (Lambda + Mangum).
Owner: P2 (Backend and infra).
"""

from fastapi import FastAPI
from mangum import Mangum

from app.schemas import (
    CaseResponse,
    CheckinsResponse,
    ClockAdvanceRequest,
    ClockAdvanceResponse,
    CreateOutageRequest,
    CreateOutageResponse,
    CreatePlanRequest,
    DashboardResponse,
    InboundRequest,
    MessagesResponse,
    PlanResponse,
    RunResponse,
    TracesResponse,
)

app = FastAPI(title="StillHere API")
# TODO(P2, §6): CORS for the Amplify origin and localhost:5173.


@app.post("/demo/reset")
def reset_demo() -> None:
    """Reseed from data/, clear cases, messages, plans and traces, clock offset to 0."""
    ...


@app.post("/outages")
def create_outage(body: CreateOutageRequest) -> CreateOutageResponse:
    """Create the outage and find affected residents (geo.point_in_polygon)."""
    ...


@app.post("/outages/{outage_id}/checkins")
def send_checkins(outage_id: str) -> CheckinsResponse:
    """Job 1 in parallel for every affected resident; cases move to awaiting_reply."""
    ...


@app.post("/inbound")
def inbound(body: InboundRequest) -> CaseResponse:
    """Same webhook shape AWS End User Messaging would call. Jobs 2 and 3, then rescore."""
    ...


@app.post("/clock/advance")
def advance_clock(body: ClockAdvanceRequest) -> ClockAdvanceResponse:
    """Move virtual time forward and run the escalation check now (Job 4)."""
    ...


@app.post("/plans")
def create_plan(body: CreatePlanRequest) -> PlanResponse:
    """Draft plan from the Job 5 agent (agent.plan_dispatch)."""
    ...


@app.post("/plans/{plan_id}/approve")
def approve_plan(plan_id: str) -> PlanResponse:
    """Human approval; cases in the plan become dispatched."""
    ...


@app.post("/runs/{run_id}/stops/{resident_id}/done")
def mark_stop_done(run_id: str, resident_id: str) -> CaseResponse:
    """Volunteer marks a stop done; the case becomes resolved."""
    ...


@app.get("/dashboard")
def dashboard(outage_id: str) -> DashboardResponse:
    """Everything the command center polls every 3 s, at virtual now."""
    ...


@app.get("/residents/{resident_id}/messages")
def resident_messages(resident_id: str) -> MessagesResponse:
    ...


@app.get("/traces")
def list_traces(limit: int = 50) -> TracesResponse:
    ...


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> RunResponse:
    """Volunteer route sheet view."""
    ...


_asgi_handler = Mangum(app)


def handler(event, context):
    """Lambda entry point (infra/template.yaml: app.main.handler).

    TODO(P2, §5): send EventBridge Scheduler events to
    escalation.run_escalation_check; everything else goes to Mangum.
    """
    return _asgi_handler(event, context)
