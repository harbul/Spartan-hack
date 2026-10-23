"""Job 5: the dispatch planner agent (Converse tool-use loop, strong model).

The agent decides who goes where and why; Amazon Location decides stop
order and road route (via tools.optimize_run). Output is a draft plan only.

Implements: PLAN.md §4 Job 5, §16 (greedy fallback planner).
Owner: P3 (AI).
"""

import logging
import time
from typing import Any

from app import bedrock, geo, tools
from app.schemas import Plan

log = logging.getLogger(__name__)
MAX_TURNS = 12
TIME_BUDGET_S = 20  # leaves room under the 30 s API limit for the greedy fallback (§17)
START = "Plan the volunteer runs for the open cases in this outage."

ITEMS = {
    "cooler": ["cooler", "ice packs"],
    "battery": ["charged battery pack"],
    "door_knock": ["phone", "printed resource center info"],
    "ride": ["seat for one"],
}


def plan_dispatch(outage_id: str) -> Plan:
    """Run the tool-use loop with prompts/planner.md and tools.AGENT_TOOLS until submit_plan.

    Every turn is a converse() call, so each one is a row in the AI Trace drawer.
    Falls back to greedy_plan() on the turn limit, the time budget or an error;
    the plan summary says so. A missing model ID is a setup error and is raised.
    """
    started = time.monotonic()
    messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": START}]}]
    first_trace = None
    try:
        for _ in range(MAX_TURNS):
            if time.monotonic() - started > TIME_BUDGET_S:
                return greedy_plan(outage_id, f"time budget of {TIME_BUDGET_S} s reached")
            result = bedrock.converse(
                "planner",
                bedrock.load_prompt("planner"),
                messages,
                strong=True,
                tools=tools.AGENT_TOOLS,
                max_tokens=2000,
                temperature=0,
            )
            first_trace = first_trace or result.trace_id
            content = result.raw["output"]["message"]["content"]
            messages.append({"role": "assistant", "content": content})
            uses = [block["toolUse"] for block in content if "toolUse" in block]
            if not uses:
                messages.append({"role": "user", "content": [{"text": "Call submit_plan with the runs."}]})
                continue
            results = []
            for use in uses:
                output = tools.run_tool(use["name"], use.get("input") or {}, outage_id)
                if isinstance(output, Plan):
                    output.trace_id = first_trace
                    return output
                results.append(
                    {
                        "toolResult": {
                            "toolUseId": use["toolUseId"],
                            "content": [{"json": output}],
                            "status": "error" if "error" in output else "success",
                        }
                    }
                )
            messages.append({"role": "user", "content": results})
        return greedy_plan(outage_id, f"no plan after {MAX_TURNS} turns")
    except bedrock.BedrockNotConfigured:
        raise
    except Exception as err:  # noqa: BLE001  (any agent failure must still leave Dana a plan)
        log.warning("planner agent failed, using the greedy plan: %s", err)
        return greedy_plan(outage_id, f"error: {type(err).__name__}")


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

    Cases that must be covered (tools.must_cover) in priority order; each goes to the
    volunteer whose last stop (or start) is nearest and who still has room.
    """
    volunteers = tools.list_volunteers()
    runs: dict[str, list[dict[str, Any]]] = {v["volunteer_id"]: [] for v in volunteers}
    last = {v["volunteer_id"]: (v["start"]["lat"], v["start"]["lng"]) for v in volunteers}
    seats = {v["volunteer_id"]: v["capacity"] for v in volunteers}
    for case in tools.list_open_cases(outage_id):  # highest priority first
        if not tools.must_cover(case):
            continue
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
