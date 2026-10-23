"""Tool schemas and implementations for the Bedrock tool-use calls.

Holds the Converse `toolSpec` definitions for the Job 5 dispatch agent and
the Job 2 forced `record_assessment` tool, plus the Python functions the
agent's tool calls run. Tool implementations call store, geo and location.

Implements: PLAN.md §4 (Job 2 tool schema, Job 5 tools).
Owner: P3 (AI).
"""

from typing import Any

from app.schemas import Assessment, Plan, Run

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

# TODO(P3, §4 Job 5): toolSpecs for the five agent tools below.
AGENT_TOOLS: list[dict[str, Any]] = []


def list_open_cases(outage_id: str) -> list[dict[str, Any]]:
    """Cases with status needs_help, escalated or silent: priority, location, needs."""
    ...


def list_volunteers() -> list[dict[str, Any]]:
    """Name, vehicle, start location, capacity."""
    ...


def find_nearest_resource(lat: float, lng: float, type: str) -> dict[str, Any]:
    """Nearest resource center or pharmacy (geo.nearest_resource)."""
    ...


def optimize_run(start: dict[str, float], stops: list[dict[str, Any]]) -> dict[str, Any]:
    """Stop order, duration, distance and geometry (location.optimize_waypoints + calculate_route)."""
    ...


def submit_plan(outage_id: str, runs: list[Run]) -> Plan:
    """Final draft plan. Ends the agent loop. Nothing is dispatched until approval."""
    ...


def run_tool(name: str, tool_input: dict[str, Any], outage_id: str) -> Any:
    """Dispatch one toolUse block from the agent to the function above."""
    ...
