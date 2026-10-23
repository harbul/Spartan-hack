"""Job 5: the dispatch planner agent (Converse tool-use loop, strong model).

The agent decides who goes where and why; Amazon Location decides stop
order and road route (via tools.optimize_run). Output is a draft plan only.

Implements: PLAN.md §4 Job 5, §16 (greedy fallback planner).
Owner: P3 (AI).
"""

from typing import Any

from app import geo, tools
from app.schemas import Plan

MAX_TURNS = 12

ITEMS = {
    "cooler": ["cooler", "ice packs"],
    "battery": ["charged battery pack"],
    "door_knock": ["phone", "printed resource center info"],
    "ride": ["seat for one"],
}


def plan_dispatch(outage_id: str) -> Plan:
    """Run the tool-use loop with prompts/planner.md and tools.AGENT_TOOLS until submit_plan."""
    ...


def _action(case: dict[str, Any]) -> str:
    if case["status"] in ("escalated", "silent"):
        return "door_knock"
    if case["needs_transport"] or "transport" in case["needs"]:
        return "ride"
    if "cooling_for_medication" in case["needs"]:
        return "cooler"
    if "power_for_device" in case["needs"]:
        return "battery"
    return "door_knock"


def greedy_plan(outage_id: str, reason: str = "") -> Plan:
    """Fallback if the agent loops or fails: priority first, then nearest neighbor.

    Cases at or above tools.COVER_PRIORITY in priority order; each goes to the
    volunteer whose last stop (or start) is nearest and who still has room.
    """
    volunteers = tools.list_volunteers()
    runs: dict[str, list[dict[str, Any]]] = {v["volunteer_id"]: [] for v in volunteers}
    last = {v["volunteer_id"]: (v["start"]["lat"], v["start"]["lng"]) for v in volunteers}
    seats = {v["volunteer_id"]: v["capacity"] for v in volunteers}
    for case in tools.list_open_cases(outage_id):
        if case["priority"] < tools.COVER_PRIORITY:
            break  # sorted by priority
        action = _action(case)
        room = [vid for vid, stops in runs.items() if len(stops) < tools.MAX_STOPS]
        if action == "ride" and not any(seats[vid] for vid in room):
            action = "door_knock"  # no seat left: check on them and arrange a ride
        if action == "ride":
            room = [vid for vid in room if seats[vid]]
        if not room:
            break  # everyone is full: the rest is the next wave
        vid = min(room, key=lambda v: geo.distance_km(*last[v], case["lat"], case["lng"]))
        seats[vid] -= action == "ride"
        last[vid] = (case["lat"], case["lng"])
        why = case["why"] or f"{case['band']} priority, needs: {', '.join(case['needs'])}"
        runs[vid].append({"resident_id": case["resident_id"], "action": action, "items": ITEMS[action], "reason": why})
    summary = "Fallback plan built in code: highest priority first, nearest volunteer with room."
    if reason:
        summary += f" (The AI planner did not finish: {reason}.)"
    return tools.submit_plan(
        outage_id, [{"volunteer_id": vid, "stops": stops} for vid, stops in runs.items() if stops], summary
    )
