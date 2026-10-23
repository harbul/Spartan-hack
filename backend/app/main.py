"""FastAPI routes for every endpoint in the API contract, plus the Lambda handler.

Routes stay thin: they call store, triage, escalation, geo, location and the
Bedrock jobs. Request and response shapes come from schemas.py.

Implements: PLAN.md §8 (API contract), §6 (Lambda + Mangum).
Owner: P2 (Backend and infra).
"""

import base64
import binascii
import uuid

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mangum import Mangum

from app import agent, bedrock, escalation, geo, store, triage
from app.schemas import (
    Case,
    CaseResponse,
    CheckinsResponse,
    ClockAdvanceRequest,
    ClockAdvanceResponse,
    CreateOutageRequest,
    CreateOutageResponse,
    Counts,
    CreatePlanRequest,
    DashboardCase,
    DashboardResponse,
    Event,
    InboundRequest,
    Message,
    MessagesResponse,
    Outage,
    PlanResponse,
    Resource,
    RunResponse,
    RunStopDetail,
    TracesResponse,
    Volunteer,
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
    outage = _outage(outage_id)
    residents = {r.resident_id: r for r in store.list_residents()}
    cases = [c for c in store.list_cases(outage_id) if c.status == "not_contacted"]
    drafts = bedrock.write_checkins([residents[c.resident_id] for c in cases], outage)
    at = escalation.now()
    ts = escalation.iso(at)
    for case in cases:
        draft = drafts[case.resident_id]
        store.add_message(
            Message(
                resident_id=case.resident_id,
                ts=ts,
                direction="out",
                channel="sms",
                text=draft.output,
                trace_id=draft.trace_id,
            )
        )
        case.status = "awaiting_reply"
        case.last_outbound_at = ts
        # First score from the profile alone; no "why" or band events yet (40 Bedrock calls saved).
        escalation.rescore_case(case, residents[case.resident_id], outage, at, explain=False, track=False)
    if cases:
        store.add_event(
            Event(outage_id=outage_id, ts=ts, type="checkins_sent", label=f"Check-ins sent to {len(cases)} residents")
        )
    return CheckinsResponse(sent=len(cases))


@app.post("/inbound")
def inbound(body: InboundRequest) -> CaseResponse:
    """Same webhook shape AWS End User Messaging would call. Jobs 2 and 3, then rescore."""
    resident = store.find_resident_by_phone(body.phone)
    if not resident:
        raise HTTPException(status_code=404, detail="Unknown phone number")
    outage = store.get_active_outage()
    case = store.get_case(outage.outage_id, resident.resident_id) if outage else None
    if not outage or not case:
        raise HTTPException(status_code=404, detail=f"{resident.name} is not in an active outage")

    at = escalation.now()
    ts = escalation.iso(at)
    image = _decode_image(body.image_b64)
    image_key = None
    if image:
        fmt = bedrock.image_format(image)
        image_key = f"replies/{resident.resident_id}/{ts}.{fmt}"
        store.put_photo(image_key, image, f"image/{fmt}")

    sent = [m for m in store.list_messages(resident.resident_id) if m.direction == "out" and m.channel == "sms"]
    # Job 6: a reply asking for medical advice (e.g. a dose) is never answered by the app; a person takes it.
    screened = bedrock.screen_reply(body.text) if body.text.strip() else None
    assessed = bedrock.assess_reply(resident, sent[-1].text if sent else "", body.text, image)
    a = assessed.output
    store.add_message(
        Message(
            resident_id=resident.resident_id,
            ts=ts,
            direction="in",
            channel="sms",
            text=body.text,
            translation_en=None if a.detected_language == "en" else a.english_translation,
            image_key=image_key,
            trace_id=assessed.trace_id,
        )
    )

    before = case.status
    case.assessment = a
    case.last_inbound_at = ts
    case.needs_review = a.confidence < triage.REVIEW_CONFIDENCE or bool(screened and screened.output)
    if before not in ("dispatched", "resolved"):
        # "unclear" still means a person answered: someone should look, not escalate.
        case.status = "ok" if a.status == "ok" else "needs_help"
    store.add_event(
        Event(
            outage_id=outage.outage_id,
            ts=ts,
            type="reply",
            label=f"{resident.name} replied",
            resident_id=resident.resident_id,
            from_status=before,
            to_status=case.status,
        )
    )
    escalation.rescore_case(case, resident, outage, at, explain=True)
    return CaseResponse(case=case)


@app.post("/clock/advance")
def advance_clock(body: ClockAdvanceRequest) -> ClockAdvanceResponse:
    """Move virtual time forward and run the escalation check now (Job 4)."""
    try:
        at = escalation.advance(body.minutes)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err)) from err
    outage = store.get_active_outage()
    escalations = _tick(outage.outage_id) if outage else []
    return ClockAdvanceResponse(now=escalation.iso(at), escalations=escalations)


@app.post("/plans")
def create_plan(body: CreatePlanRequest) -> PlanResponse:
    """Draft plan from the Job 5 agent (agent.plan_dispatch)."""
    _outage(body.outage_id)
    if not any(c.status in ("needs_help", "escalated", "silent") for c in store.list_cases(body.outage_id)):
        raise HTTPException(status_code=409, detail="No open cases to plan for")
    plan = agent.plan_dispatch(body.outage_id)
    store.put_plan(plan)
    stops = sum(len(r.stops) for r in plan.runs)
    label = f"Plan drafted: {stops} stops for {len(plan.runs)} volunteers"
    if plan.uncovered:
        label += f", {len(plan.uncovered)} for the next wave"
    store.add_event(Event(outage_id=plan.outage_id, ts=escalation.iso(escalation.now()), type="plan_drafted", label=label))
    return PlanResponse(plan=plan)


@app.post("/plans/{plan_id}/approve")
def approve_plan(plan_id: str) -> PlanResponse:
    """Human approval; cases in the plan become dispatched."""
    plan = store.get_plan(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"No plan {plan_id}")
    if plan.status == "approved":
        return PlanResponse(plan=plan)
    plan.status = "approved"
    store.put_plan(plan)
    for run in plan.runs:
        for stop in run.stops:
            case = store.get_case(plan.outage_id, stop.resident_id)
            if case and case.status != "resolved":
                case.status = "dispatched"
                store.put_case(case)
    stops = sum(len(r.stops) for r in plan.runs)
    store.add_event(
        Event(
            outage_id=plan.outage_id,
            ts=escalation.iso(escalation.now()),
            type="plan_approved",
            label=f"Plan approved: {stops} stops dispatched to {len(plan.runs)} volunteers",
        )
    )
    return PlanResponse(plan=plan)


@app.post("/runs/{run_id}/stops/{resident_id}/done")
def mark_stop_done(run_id: str, resident_id: str) -> CaseResponse:
    """Volunteer marks a stop done; the case becomes resolved."""
    plan, run = _run(run_id)
    stop = next((s for s in run.stops if s.resident_id == resident_id), None)
    if not stop:
        raise HTTPException(status_code=404, detail=f"{resident_id} is not a stop on {run_id}")
    if plan.status != "approved":
        raise HTTPException(status_code=409, detail="The plan is not approved yet")
    case = store.get_case(plan.outage_id, resident_id)
    resident = store.get_resident(resident_id)
    if case.status != "resolved":
        before = case.status
        case.status = "resolved"
        store.put_case(case)
        store.add_event(
            Event(
                outage_id=plan.outage_id,
                ts=escalation.iso(escalation.now()),
                type="stop_done",
                label=f"{resident.name}: {stop.action.replace('_', ' ')} done",
                resident_id=resident_id,
                from_status=before,
                to_status="resolved",
            )
        )
    return CaseResponse(case=case)


@app.get("/dashboard")
def dashboard(outage_id: str | None = None) -> DashboardResponse:
    """Everything the command center polls every 3 s, at virtual now.

    `outage_id` is optional: without it, the active outage (the demo runs one).
    """
    at = escalation.now()
    outage = store.get_outage(outage_id) if outage_id else store.get_active_outage()
    resources = [Resource.model_validate(r) for r in store.get_config("resources") or []]
    volunteers = [Volunteer.model_validate(v) for v in store.get_config("volunteers") or []]
    cases: list[DashboardCase] = []
    if outage:
        residents = {r.resident_id: r for r in store.list_residents()}
        for case in store.list_cases(outage.outage_id):
            resident = residents[case.resident_id]
            _, backup = triage.score_case(resident, case, outage, at)
            cases.append(DashboardCase(**case.model_dump(), resident=resident, backup_hours_left=backup))
    return DashboardResponse(
        now=escalation.iso(at),
        outage=outage,
        counts=_counts(cases),
        cases=cases,
        events=store.list_events(outage.outage_id) if outage else [],
        plan=store.latest_plan(outage.outage_id) if outage else None,
        resources=resources,
        volunteers=volunteers,
    )


@app.get("/residents/{resident_id}/messages")
def resident_messages(resident_id: str) -> MessagesResponse:
    return MessagesResponse(messages=store.list_messages(resident_id))


@app.get("/traces")
def list_traces(limit: int = 50) -> TracesResponse:
    return TracesResponse(traces=store.list_traces(min(max(limit, 1), 200)))


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> RunResponse:
    """Volunteer route sheet view: the run, its volunteer, and each stop's resident and status."""
    plan, run = _run(run_id)
    residents = {r.resident_id: r for r in store.list_residents()}
    cases = {c.resident_id: c for c in store.list_cases(plan.outage_id)}
    volunteer = next(
        (Volunteer.model_validate(v) for v in store.get_config("volunteers") or [] if v["volunteer_id"] == run.volunteer),
        None,
    )
    details = [
        RunStopDetail(
            resident_id=s.resident_id,
            name=residents[s.resident_id].name,
            address=residents[s.resident_id].address,
            lat=residents[s.resident_id].lat,
            lng=residents[s.resident_id].lng,
            status=cases[s.resident_id].status,
        )
        for s in run.stops
    ]
    return RunResponse(run=run, volunteer=volunteer, stops_detail=details)


# --- helpers ------------------------------------------------------------------


def _outage(outage_id: str) -> Outage:
    outage = store.get_outage(outage_id)
    if not outage:
        raise HTTPException(status_code=404, detail=f"No outage {outage_id}")
    return outage


def _run(run_id: str):
    found = store.find_run(run_id)
    if not found:
        raise HTTPException(status_code=404, detail=f"No run {run_id}")
    return found


def _decode_image(image_b64: str | None) -> bytes | None:
    """Base64 photo from the phone simulator; a data-URL prefix is allowed."""
    if not image_b64:
        return None
    try:
        return base64.b64decode(image_b64.split(",", 1)[-1], validate=True)
    except (binascii.Error, ValueError) as err:
        raise HTTPException(status_code=422, detail="image_b64 is not valid base64") from err


def _counts(cases: list[Case]) -> Counts:
    """Same rule as the frontend's categoryOf (frontend/src/components/status.ts)."""
    open_help = [c for c in cases if c.status in ("needs_help", "dispatched")]
    return Counts(
        safe=sum(c.status in ("ok", "resolved") for c in cases),
        needs_help=sum(c.band != "Critical" for c in open_help),
        critical=sum(c.band == "Critical" for c in open_help),
        no_reply=sum(c.status in ("awaiting_reply", "escalated", "silent") for c in cases),
    )


def _tick(outage_id: str):
    """What time passing does: escalate silent cases, then rescore everyone."""
    escalations = escalation.run_escalation_check(outage_id)
    escalation.rescore_open_cases(outage_id)
    return escalations


SCHEDULED_EVENT = {"stillhere": "escalation_check"}  # the Input of the 1-minute schedule

_asgi_handler = Mangum(app)


def handler(event, context):
    """Lambda entry point (infra/template.yaml: app.main.handler).

    The EventBridge schedule runs the escalation check; everything else goes to Mangum.
    """
    if isinstance(event, dict) and event.get("stillhere") == SCHEDULED_EVENT["stillhere"]:
        outage = store.get_active_outage()
        return {"escalations": len(_tick(outage.outage_id)) if outage else 0}
    return _asgi_handler(event, context)
