"""FastAPI routes for every endpoint in the API contract, plus the Lambda handler.

Routes stay thin: they call store, triage, escalation, geo, location and the
Bedrock jobs. Request and response shapes come from schemas.py.

Implements: PLAN.md §8 (API contract), §6 (Lambda + Mangum).
Owner: P2 (Backend and infra).
"""

import uuid

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app import bedrock, geo, store
from app.schemas import (
    Case,
    CaseResponse,
    CheckinsResponse,
    ClockAdvanceRequest,
    ClockAdvanceResponse,
    CreateOutageRequest,
    CreateOutageResponse,
    CreatePlanRequest,
    DashboardResponse,
    Event,
    InboundRequest,
    MessagesResponse,
    Outage,
    PlanResponse,
    RunResponse,
    TracesResponse,
)

app = FastAPI(title="StillHere API")

# Local runs (uvicorn). In Lambda, API Gateway answers CORS itself (infra/template.yaml).
# TODO(P2, §6): restrict both to the Amplify origin and localhost:5173.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["content-type"],
)


# Clear errors instead of a bare 500, so a missing setting is obvious from the frontend.


@app.exception_handler(bedrock.BedrockNotConfigured)
@app.exception_handler(store.StoreNotConfigured)
def not_configured(request: Request, err: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(err)})


@app.exception_handler(ClientError)
def aws_client_error(request: Request, err: ClientError) -> JSONResponse:
    # e.g. AccessDeniedException (model access not granted), ResourceNotFoundException (table)
    error = err.response.get("Error", {})
    detail = f"{err.operation_name} {error.get('Code')}: {error.get('Message')}"
    return JSONResponse(status_code=502, content={"detail": detail})


@app.exception_handler(BotoCoreError)
def aws_setup_error(request: Request, err: BotoCoreError) -> JSONResponse:
    # e.g. no AWS credentials or region locally
    return JSONResponse(status_code=502, content={"detail": f"AWS: {err}"})


@app.get("/health")
def health() -> dict:
    return {"ok": True}


# --- Skeleton / debug route (H0-H1 gate). The real §8 routes replace it; delete then.


@app.get("/hello-bedrock")
def hello_bedrock() -> dict:
    """One real Bedrock call through converse(), to prove the deploy reaches the model."""
    result = bedrock.converse(
        job="hello",
        system="You are the AI inside StillHere, an emergency response command center.",
        messages=[
            {
                "role": "user",
                "content": [{"text": "In one short sentence, say hello to the StillHere team."}],
            }
        ],
        max_tokens=100,
    )
    return {
        "reply": result.text,
        "model_id": result.model_id,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


# --- §8 API contract


@app.post("/demo/reset")
def reset_demo() -> None:
    """Reseed from data/, clear cases, messages, plans and traces, clock offset to 0."""
    store.reset_demo()


@app.post("/outages")
def create_outage(body: CreateOutageRequest) -> CreateOutageResponse:
    """Create the outage and find affected residents (geo.point_in_polygon)."""
    affected = [
        r.resident_id
        for r in store.list_residents()
        if geo.point_in_polygon(r.lat, r.lng, body.polygon)
    ]
    outage = Outage(
        outage_id=f"out-{uuid.uuid4().hex[:8]}",
        name=body.name,
        polygon=body.polygon,
        starts_at=body.starts_at,
        est_restore_at=body.est_restore_at,
        affected_ids=affected,
        status="active",
    )
    store.put_outage(outage)
    store.put_cases(
        [
            Case(outage_id=outage.outage_id, resident_id=rid, status="not_contacted", priority=0, band="OK")
            for rid in affected
        ]
    )
    store.add_event(
        Event(
            outage_id=outage.outage_id,
            ts=body.starts_at,
            type="outage_started",
            label=f"Outage started: {len(affected)} registered residents affected",
        )
    )
    return CreateOutageResponse(outage_id=outage.outage_id, affected=affected)


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
