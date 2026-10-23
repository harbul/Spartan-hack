"""Tests for the Job 5 tool-use loop with a scripted model (no AWS calls).

Implements: PLAN.md §4 Job 5 (agent), §16 (greedy fallback), §17 (agent time budget).
Owner: P3 (AI).
"""

import pytest
from test_tools import world  # noqa: F401  (fixture: seeded tables, 4 open cases, no Location)

from app import agent, bedrock


def tool_use(i, name, tool_input=None):
    return {"toolUse": {"toolUseId": f"tu-{i}", "name": name, "input": tool_input or {}}}


def turn(*blocks):
    return {"output": {"message": {"role": "assistant", "content": list(blocks)}}, "stopReason": "tool_use"}


def stop(rid, action):
    return {"resident_id": rid, "action": action, "items": ["x"], "reason": f"because {rid}"}


GOOD_RUNS = [
    {"volunteer_id": "vol-1", "stops": [stop("res-005", "door_knock"), stop("res-001", "battery"), stop("res-002", "cooler")]},
    {"volunteer_id": "vol-3", "stops": [stop("res-003", "ride")]},
]


@pytest.fixture
def model(monkeypatch):
    """Plays scripted turns; records the messages each call saw."""
    script, seen = [], []

    def fake(job, system, messages, **kwargs):
        assert job == "planner" and kwargs["strong"] and kwargs["tools"]
        seen.append([dict(m) for m in messages])
        raw = script.pop(0) if script else turn(tool_use(99, "list_open_cases"))
        return bedrock.ConverseResult("", "m", 1, 1, 1, "tool_use", raw, f"tr-{len(seen)}")

    monkeypatch.setattr(bedrock, "converse", fake)
    return script, seen


def test_agent_fixes_a_rejected_plan(world, model):  # noqa: F811
    script, seen = model
    script += [
        turn(tool_use(1, "list_open_cases"), tool_use(2, "list_volunteers")),
        turn(tool_use(3, "optimize_run", {"volunteer_id": "vol-1", "resident_ids": ["res-005", "res-001", "res-002"]})),
        turn(tool_use(4, "submit_plan", {"summary": "s", "runs": GOOD_RUNS[:1]})),  # Harold left out: rejected
        turn(tool_use(5, "submit_plan", {"summary": "All four covered.", "runs": GOOD_RUNS})),
    ]
    plan = agent.plan_dispatch("out-1")
    assert plan.summary.startswith("All four covered") and plan.trace_id == "tr-1"
    assert sorted(s.resident_id for r in plan.runs for s in r.stops) == ["res-001", "res-002", "res-003", "res-005"]

    results = seen[1][-1]["content"]  # what the model got back after turn 1
    assert [r["toolResult"]["toolUseId"] for r in results] == ["tu-1", "tu-2"]
    assert len(results[0]["toolResult"]["content"][0]["json"]["cases"]) == 4
    rejection = seen[3][-1]["content"][0]["toolResult"]
    assert rejection["status"] == "error" and "res-003" in " ".join(rejection["content"][0]["json"]["problems"])


def test_turn_limit_falls_back_to_greedy(world, model):  # noqa: F811
    plan = agent.plan_dispatch("out-1")  # the model only ever lists cases
    assert len(model[1]) == agent.MAX_TURNS
    assert f"no plan after {agent.MAX_TURNS} turns" in plan.summary and plan.uncovered == []


def test_time_budget_falls_back_without_calling_the_model(world, model, monkeypatch):  # noqa: F811
    monkeypatch.setattr(agent, "TIME_BUDGET_S", -1)
    assert "time budget" in agent.plan_dispatch("out-1").summary and model[1] == []


def test_errors_fall_back_but_setup_errors_surface(world, monkeypatch):  # noqa: F811
    def broken(*args, **kwargs):
        raise RuntimeError("throttled")

    monkeypatch.setattr(bedrock, "converse", broken)
    assert "error: RuntimeError" in agent.plan_dispatch("out-1").summary

    def unconfigured(*args, **kwargs):
        raise bedrock.BedrockNotConfigured("BEDROCK_STRONG_MODEL_ID is not set")

    monkeypatch.setattr(bedrock, "converse", unconfigured)
    with pytest.raises(bedrock.BedrockNotConfigured):
        agent.plan_dispatch("out-1")


def test_a_reply_without_tools_gets_nudged(world, model):  # noqa: F811
    script, seen = model
    script += [
        {"output": {"message": {"role": "assistant", "content": [{"text": "Here is my plan..."}]}}, "stopReason": "end_turn"},
        turn(tool_use(1, "submit_plan", {"summary": "ok", "runs": GOOD_RUNS})),
    ]
    assert agent.plan_dispatch("out-1").summary == "ok (Routes are straight lines: Amazon Location was unavailable.)"
    assert seen[1][-1]["content"] == [{"text": "Call submit_plan with the runs."}]
