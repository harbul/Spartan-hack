"""Tool schemas and implementations for the Bedrock tool-use calls.

Holds the Converse `toolSpec` definitions for the Job 5 dispatch agent and
the Job 2 forced `record_assessment` tool, plus the Python functions the
agent's tool calls run. Tool implementations call store, geo and location.

Implements: PLAN.md §4 (Job 2 tool schema, Job 5 tools).
Owner: P3 (AI).
"""

from typing import Any

from app.schemas import Plan, Run

# TODO(P3, §4 Job 2): toolSpec for record_assessment.
# Build inputSchema from schemas.Assessment.model_json_schema() so it can't drift.
RECORD_ASSESSMENT: dict[str, Any] = {}

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
