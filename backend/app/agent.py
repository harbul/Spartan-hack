"""Job 5: the dispatch planner agent (Converse tool-use loop, strong model).

The agent decides who goes where and why; Amazon Location decides stop
order and road route (via tools.optimize_run). Output is a draft plan only.

Implements: PLAN.md §4 Job 5, §16 (greedy fallback planner).
Owner: P3 (AI).
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any

from app import bedrock, geo, store, tools
from app.schemas import Plan

log = logging.getLogger(__name__)
MAX_TURNS = 12
# Hard deadline for the agent. On real Bedrock a Sonnet turn takes ~7 s and a turn can't be cut short,
# so the agent runs in a worker thread and the greedy plan (+ routes, ~3-5 s) starts on time.
# 18 s + fallback stays under the 30 s API limit (§17); the abandoned turn finishes in the background.
TIME_BUDGET_S = 18
START = (
    "Plan the volunteer runs for the open cases in this outage. The open cases, volunteers and resource "
    "centers are below, so you can call submit_plan right away."
)
_POOL = ThreadPoolExecutor(max_workers=2, thread_name_prefix="planner")

# What the agent needs from each open case (tools.list_open_cases has a few more fields).
CASE_FIELDS = ("resident_id", "name", "priority", "band", "status", "needs", "needs_transport", "devices",
               "lives_alone", "why", "lat", "lng")


def _start_message(outage_id: str) -> str:
    """START plus the data the first three tool calls used to fetch, saving two ~7 s turns."""
    data = {
        "open_cases": [{k: c[k] for k in CASE_FIELDS} for c in tools.list_open_cases(outage_id)],
        "volunteers": tools.list_volunteers(),
        "resources": store.get_config("resources") or [],
    }
    return f"{START}\n\n{json.dumps(data, ensure_ascii=False, default=str)}"



def plan_dispatch(outage_id: str) -> Plan:
    """Run the tool-use loop with prompts/planner.md and tools.AGENT_TOOLS until submit_plan.

    Every turn is a converse() call, so each one is a row in the AI Trace drawer.
    Falls back to greedy_plan() on the turn limit, the time budget or an error;
    the plan summary says so. A missing model ID is a setup error and is raised.
    """
    started = time.monotonic()
    future = _POOL.submit(_agent_loop, outage_id, started)
    try:
        return future.result(timeout=max(TIME_BUDGET_S - (time.monotonic() - started), 0))
    except FutureTimeout:
        return greedy_plan(outage_id, f"time budget of {TIME_BUDGET_S} s reached")
    except bedrock.BedrockNotConfigured:
        raise
    except Exception as err:  # noqa: BLE001  (any agent failure must still leave Dana a plan)
        log.warning("planner agent failed, using the greedy plan: %s", err)
        return greedy_plan(outage_id, f"error: {type(err).__name__}")


def _agent_loop(outage_id: str, started: float) -> Plan:
    """The tool-use loop itself, run in a worker thread by plan_dispatch()."""
    messages: list[dict[str, Any]] = [{"role": "user", "content": [{"text": _start_message(outage_id)}]}]
    first_trace = None
    for _ in range(MAX_TURNS):
        if time.monotonic() - started > TIME_BUDGET_S:
            return greedy_plan(outage_id, f"time budget of {TIME_BUDGET_S} s reached")
        result = bedrock.converse(
            "planner",
            bedrock.load_prompt("planner"),
            messages,
            strong=True,
            tools=tools.AGENT_TOOLS,
            # Forced: on real Bedrock, Sonnet wrote ~2,000 tokens of prose around the call (17-22 s);
            # forced, the whole plan is ~1,000 tokens (~10 s). The data is in the first message.
            tool_choice={"tool": {"name": "submit_plan"}},
            max_tokens=4000,
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
        action = tools.default_action(case)
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
        why = tools.default_reason(case)
        runs[vid].append({"resident_id": case["resident_id"], "action": action, "items": tools.DEFAULT_ITEMS[action], "reason": why})
    summary = "Fallback plan built in code: highest priority first, nearest volunteer with room."
    if reason:
        summary += f" (The AI planner did not finish: {reason}.)"
    return tools.submit_plan(
        outage_id, [{"volunteer_id": vid, "stops": stops} for vid, stops in runs.items() if stops], summary
    )
