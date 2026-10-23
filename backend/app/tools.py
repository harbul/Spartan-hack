"""Tool schemas and implementations for the Bedrock tool-use calls.

Holds the Converse `toolSpec` definitions for the Job 5 dispatch agent and
the Job 2 forced `record_assessment` tool, plus the Python functions the
agent's tool calls run. Tool implementations call store, geo and location.

Implements: PLAN.md §4 (Job 2 tool schema, Job 5 tools).
Owner: P3 (AI).
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any, get_args

from app import geo, location, store
from app.schemas import Assessment, Plan, Resource, Run, Stop, StopAction, Volunteer

# --- Job 2: forced `record_assessment` tool ----------------------------------------

# One hint per Assessment field. A field without a hint fails at import, so the
# tool schema can't drift from schemas.Assessment.
_ASSESSMENT_HINTS = {
    "status": "ok = safe for now; needs_help = asks for or clearly needs help; unclear = can't tell",
    "needs": "Every need stated or clearly implied; empty when status is ok",
    "supply_hours_left": "Hours their medicine or equipment can last, only if the reply or photo says; else null",
    "needs_transport": "True only if they need a ride or can't get out on their own",
    "distress_level": "0 calm, 1 worried, 2 struggling or near-term risk, 3 emergency now",
    "detected_language": "ISO 639-1 code of the reply, e.g. en, es, vi",
    "english_translation": "Faithful English translation of the whole reply",
    "key_quote": "The most important words, copied exactly in the original language",
    "confidence": "0-1, how sure you are of status and needs; below 0.6 goes to human review",
    "reasoning": "1-2 sentences in English",
}


def _assessment_input_schema() -> dict[str, Any]:
    schema = Assessment.model_json_schema()
    schema.pop("title", None)
    schema.pop("description", None)
    for name, prop in schema["properties"].items():
        prop.pop("title", None)
        prop["description"] = _ASSESSMENT_HINTS[name]
    schema["properties"]["distress_level"].update(minimum=0, maximum=3)
    schema["properties"]["confidence"].update(minimum=0, maximum=1)
    return schema


RECORD_ASSESSMENT: dict[str, Any] = {
    "toolSpec": {
        "name": "record_assessment",
        "description": "Record the structured assessment of one resident reply.",
        "inputSchema": {"json": _assessment_input_schema()},
    }
}

# --- Job 5: dispatch agent tools ----------------------------------------------------

MAX_STOPS = 6  # per volunteer (§4 Job 5)
COVER_PRIORITY = 60  # every case at or above this should be in a run


def must_cover(case: dict) -> bool:
    """Priority 60+ (§4 Job 5), and every silent (L3) case: a door-knock in the next plan (§5)."""
    return case["priority"] >= COVER_PRIORITY or case["status"] == "silent"

OPEN_STATUSES = ("needs_help", "escalated", "silent")
ACTIONS = list(get_args(StopAction))


def _spec(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    schema = {"type": "object", "properties": properties, "required": required}
    return {"toolSpec": {"name": name, "description": description, "inputSchema": {"json": schema}}}


AGENT_TOOLS: list[dict[str, Any]] = [
    _spec("list_open_cases", "Open cases (needs_help, escalated, silent), highest priority first.", {}, []),
    _spec("list_volunteers", "Volunteers with vehicle, start location and passenger seats (capacity).", {}, []),
    _spec(
        "find_nearest_resource",
        "Nearest resource center or pharmacy to a point.",
        {
            "lat": {"type": "number"},
            "lng": {"type": "number"},
            "type": {"type": "string", "enum": ["resource_center", "pharmacy"]},
        },
        ["lat", "lng", "type"],
    ),
    _spec(
        "optimize_run",
        "Amazon Location: fastest stop order, drive time and distance for one volunteer's stops.",
        {"volunteer_id": {"type": "string"}, "resident_ids": {"type": "array", "items": {"type": "string"}}},
        ["volunteer_id", "resident_ids"],
    ),
    _spec(
        "submit_plan",
        "Submit the draft plan. Rules are checked; if any fail you get the problems back to fix.",
        {
            "summary": {"type": "string", "description": "2-3 sentences for the coordinator"},
            "runs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "volunteer_id": {"type": "string"},
                        "stops": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "resident_id": {"type": "string"},
                                    "action": {"type": "string", "enum": ACTIONS},
                                    "items": {"type": "array", "items": {"type": "string"}},
                                    "reason": {"type": "string", "description": "one line: why this stop"},
                                },
                                "required": ["resident_id", "action", "items", "reason"],
                            },
                        },
                    },
                    "required": ["volunteer_id", "stops"],
                },
            },
        },
        ["summary", "runs"],
    ),
]


class PlanError(ValueError):
    """submit_plan broke a rule; `problems` go back to the agent so it can fix them."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def list_open_cases(outage_id: str) -> list[dict[str, Any]]:
    """Cases with status needs_help, escalated or silent: priority, location, needs."""
    residents = {r.resident_id: r for r in store.list_residents()}
    rows = []
    for case in store.list_cases(outage_id):
        if case.status not in OPEN_STATUSES:
            continue
        r = residents[case.resident_id]
        a = case.assessment
        rows.append(
            {
                "resident_id": r.resident_id,
                "name": r.name,
                "age": r.age,
                "priority": case.priority,
                "band": case.band,
                "status": case.status,
                "escalation_level": case.escalation_level,
                "needs": a.needs if a and a.needs else ["welfare_check"],
                "needs_transport": bool(a and a.needs_transport),
                "devices": r.devices,
                "lives_alone": r.lives_alone,
                "language": r.language,
                "why": case.rationale,
                "lat": r.lat,
                "lng": r.lng,
            }
        )
    return sorted(rows, key=lambda row: row["priority"], reverse=True)


def list_volunteers() -> list[dict[str, Any]]:
    """Name, vehicle, start location, capacity."""
    return [Volunteer.model_validate(v).model_dump() for v in store.get_config("volunteers") or []]


def find_nearest_resource(lat: float, lng: float, type: str) -> dict[str, Any]:
    """Nearest resource center or pharmacy (geo.nearest_resource)."""
    resources = [Resource.model_validate(r) for r in store.get_config("resources") or []]
    found = geo.nearest_resource(lat, lng, type, resources)
    if not found:
        return {"error": f"no {type} found"}
    km = geo.distance_km(lat, lng, found.lat, found.lng)
    return found.model_dump() | {"distance_km": round(km, 2)}


@lru_cache(maxsize=128)
def _route(start: tuple[float, float], points: tuple[tuple[float, float], ...]) -> tuple[tuple[int, ...], dict[str, Any]]:
    """Order + route for one run, cached so submit_plan reuses the agent's optimize_run calls."""
    as_dict = lambda p: {"lat": p[0], "lng": p[1]}  # noqa: E731
    order, order_fallback = location.optimize_waypoints(as_dict(start), [as_dict(p) for p in points])
    route = location.calculate_route([as_dict(start)] + [as_dict(points[i]) for i in order])
    return tuple(order), route | {"fallback": route["fallback"] or order_fallback}


def _run_points(volunteer: dict[str, Any], resident_ids: list[str], residents: dict) -> tuple:
    start = (volunteer["start"]["lat"], volunteer["start"]["lng"])
    return start, tuple((residents[r].lat, residents[r].lng) for r in resident_ids)


def optimize_run(volunteer_id: str, resident_ids: list[str]) -> dict[str, Any]:
    """Stop order, duration, distance (location.optimize_waypoints + calculate_route). No geometry: it
    would only cost the agent tokens; submit_plan adds it."""
    volunteers = {v["volunteer_id"]: v for v in list_volunteers()}
    residents = {r.resident_id: r for r in store.list_residents()}
    unknown = [r for r in resident_ids if r not in residents]
    if volunteer_id not in volunteers or unknown or not resident_ids:
        return {"error": f"unknown volunteer {volunteer_id!r} or residents {unknown}, or no stops"}
    order, route = _route(*_run_points(volunteers[volunteer_id], resident_ids, residents))
    return {
        "order": [resident_ids[i] for i in order],
        "duration_min": route["duration_min"],
        "distance_km": route["distance_km"],
        "straight_line_fallback": route["fallback"],
    }


def submit_plan(outage_id: str, runs: list[dict[str, Any]], summary: str, trace_id: str | None = None) -> Plan:
    """Final draft plan. Ends the agent loop. Nothing is dispatched until approval.

    Checks the §4 rules in code and raises PlanError with every problem found.
    Each run's stops are put in Amazon Location's order, with its road geometry.
    """
    cases = {c["resident_id"]: c for c in list_open_cases(outage_id)}
    volunteers = {v["volunteer_id"]: v for v in list_volunteers()}
    problems: list[str] = []
    used_volunteers: set[str] = set()
    covered: list[str] = []
    for run in runs:
        vid = run.get("volunteer_id")
        stops = run.get("stops") or []
        if vid not in volunteers:
            problems.append(f"unknown volunteer {vid!r}")
            continue
        if vid in used_volunteers:
            problems.append(f"{vid} has more than one run; merge them")
        used_volunteers.add(vid)
        if len(stops) > MAX_STOPS:
            problems.append(f"{vid} has {len(stops)} stops; the limit is {MAX_STOPS}")
        rides = sum(1 for s in stops if s.get("action") == "ride")
        if rides > volunteers[vid]["capacity"]:
            problems.append(f"{vid} has {rides} rides but {volunteers[vid]['capacity']} seat(s)")
        for stop in stops:
            rid = stop.get("resident_id")
            if rid not in cases:
                problems.append(f"{rid!r} is not an open case")
            elif rid in covered:
                problems.append(f"{rid} is in more than one run")
            else:
                covered.append(rid)
            if stop.get("action") not in ACTIONS:
                problems.append(f"{rid}: action must be one of {ACTIONS}")
    uncovered = [c for c in cases.values() if must_cover(c) and c["resident_id"] not in covered]
    if any(c["band"] == "Critical" for c in uncovered) and any(cases[r]["band"] != "Critical" for r in covered if r in cases):
        problems.append("a Critical case is left out while a lower-priority case is covered: cover Critical first")
    spare = sum(MAX_STOPS - len(r.get("stops") or []) for r in runs if r.get("volunteer_id") in volunteers)
    spare += MAX_STOPS * len(set(volunteers) - used_volunteers)
    if uncovered and spare > 0:
        problems.append(
            f"{len(uncovered)} case(s) with priority >= {COVER_PRIORITY} or silent are not covered but there is room for "
            f"{spare} more stop(s): {', '.join(c['resident_id'] for c in uncovered)}"
        )
    if problems:
        raise PlanError(problems)

    residents = {r.resident_id: r for r in store.list_residents()}

    def build(run: dict[str, Any]) -> tuple[Run, bool]:
        volunteer = volunteers[run["volunteer_id"]]
        ids = [s["resident_id"] for s in run["stops"]]
        order, route = _route(*_run_points(volunteer, ids, residents))
        by_id = {s["resident_id"]: s for s in run["stops"]}
        return Run(
            run_id=f"run-{uuid.uuid4().hex[:8]}",
            volunteer=volunteer["volunteer_id"],
            vehicle=volunteer["vehicle"],
            stops=[Stop(**{k: by_id[ids[i]][k] for k in ("resident_id", "action", "items", "reason")}) for i in order],
            geometry=route["geometry"],
            duration_min=route["duration_min"],
        ), route["fallback"]

    with ThreadPoolExecutor(max_workers=4) as pool:
        built = list(pool.map(build, [r for r in runs if r["stops"]]))
    if any(fallback for _, fallback in built):
        summary += " (Routes are straight lines: Amazon Location was unavailable.)"
    return Plan(
        plan_id=f"plan-{datetime.now(timezone.utc):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:4]}",
        outage_id=outage_id,
        status="draft",
        runs=[run for run, _ in built],
        summary=summary,
        trace_id=trace_id,
        uncovered=[c["resident_id"] for c in uncovered],
    )


def run_tool(name: str, tool_input: dict[str, Any], outage_id: str) -> Any:
    """Dispatch one toolUse block from the agent. submit_plan returns a Plan; everything
    else (and every error) returns a JSON-able dict for the toolResult."""
    try:
        if name == "list_open_cases":
            return {"cases": list_open_cases(outage_id)}
        if name == "list_volunteers":
            return {"volunteers": list_volunteers()}
        if name == "find_nearest_resource":
            return find_nearest_resource(tool_input["lat"], tool_input["lng"], tool_input["type"])
        if name == "optimize_run":
            return optimize_run(tool_input["volunteer_id"], list(tool_input["resident_ids"]))
        if name == "submit_plan":
            return submit_plan(outage_id, tool_input["runs"], tool_input.get("summary", ""))
        return {"error": f"unknown tool {name!r}"}
    except PlanError as err:
        return {"error": "plan rejected, fix and submit again", "problems": err.problems}
    except (KeyError, TypeError, ValueError) as err:
        return {"error": f"bad input for {name}: {err}"}
