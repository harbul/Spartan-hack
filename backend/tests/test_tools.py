"""Tests for the Job 5 agent tools, the plan rules in submit_plan, and the greedy fallback planner.

Amazon Location is forced to fail, so routes use the straight-line fallback (no AWS calls).
Implements: PLAN.md §4 Job 5, §16 (greedy planner, Location fallback).
Owner: P3 (AI).
"""

import pytest
from botocore.exceptions import NoCredentialsError

from app import agent, location, store, tools
from app.schemas import Assessment, Case, Outage

OUTAGE = Outage(outage_id="out-1", name="t", polygon={}, starts_at="2026-10-24T01:00:00Z",
                est_restore_at="2026-10-24T15:00:00Z", affected_ids=[], status="active")


def assessment(needs, transport=False):
    return Assessment(status="needs_help", needs=needs, supply_hours_left=None, needs_transport=transport,
                      distress_level=1, detected_language="en", english_translation="", key_quote="",
                      confidence=0.9, reasoning="")


def put(rid, status, priority, band, a=None):
    store.put_case(Case(outage_id="out-1", resident_id=rid, status=status, priority=priority, band=band,
                        assessment=a, rationale=f"why {rid}"))


class NoLocation:
    def __getattr__(self, name):
        def fail(**kwargs):
            raise NoCredentialsError()
        return fail


@pytest.fixture
def world(tables, monkeypatch):
    tools._route.cache_clear()
    monkeypatch.setattr(location, "_client", lambda: NoLocation())
    store.reset_demo()
    store.put_outage(OUTAGE)
    put("res-001", "needs_help", 90, "Critical", assessment(["power_for_device"]))  # Minh
    put("res-002", "needs_help", 70, "High", assessment(["cooling_for_medication"]))  # Rosa
    put("res-003", "needs_help", 65, "High", assessment(["transport"], transport=True))  # Harold
    put("res-004", "ok", 7, "OK")  # Denise
    put("res-005", "silent", 105, "Critical")  # Lupe


def stop(rid, action="door_knock"):
    return {"resident_id": rid, "action": action, "items": [], "reason": "r"}


def test_open_cases_highest_priority_first(world):
    cases = tools.list_open_cases("out-1")
    assert [c["resident_id"] for c in cases] == ["res-005", "res-001", "res-002", "res-003"]
    assert cases[0]["needs"] == ["welfare_check"] and cases[3]["needs_transport"]


def test_optimize_run_falls_back_to_straight_lines(world):
    result = tools.optimize_run("vol-1", ["res-005", "res-001", "res-002"])
    assert sorted(result["order"]) == ["res-001", "res-002", "res-005"]
    assert result["straight_line_fallback"] and result["distance_km"] > 0


def test_valid_plan_is_ordered_and_routed(world):
    plan = tools.submit_plan("out-1", [
        {"volunteer_id": "vol-1", "stops": [stop("res-005"), stop("res-001", "battery"), stop("res-002", "cooler")]},
        {"volunteer_id": "vol-3", "stops": [stop("res-003", "ride")]},
    ], "summary")
    assert plan.status == "draft" and plan.uncovered == []
    first = plan.runs[0]
    assert sorted(s.resident_id for s in first.stops) == ["res-001", "res-002", "res-005"]
    assert first.geometry["type"] == "LineString" and len(first.geometry["coordinates"]) == 4
    assert "straight lines" in plan.summary


@pytest.mark.parametrize("runs, problem", [
    ([{"volunteer_id": "vol-9", "stops": []}], "unknown volunteer"),
    ([{"volunteer_id": "vol-1", "stops": [stop("res-004")]}], "not an open case"),
    ([{"volunteer_id": "vol-1", "stops": [stop(r) for r in ["res-001", "res-002", "res-003", "res-005"] * 2]}], "the limit is 6"),
    ([{"volunteer_id": "vol-3", "stops": [stop("res-003", "ride"), stop("res-002", "ride")]}], "seat"),
    ([{"volunteer_id": "vol-1", "stops": [stop("res-001", "teleport")]}], "action must be one of"),
    ([{"volunteer_id": "vol-1", "stops": [stop("res-002"), stop("res-003")]}], "cover Critical first"),
    ([{"volunteer_id": "vol-1", "stops": [stop("res-005"), stop("res-001")]}], "not covered but there is room"),
])
def test_plan_rules(world, runs, problem):
    with pytest.raises(tools.PlanError) as err:
        tools.submit_plan("out-1", runs, "s")
    assert any(problem in p for p in err.value.problems)


def test_run_tool_reports_errors_instead_of_raising(world):
    assert "unknown tool" in tools.run_tool("teleport", {}, "out-1")["error"]
    assert "bad input" in tools.run_tool("find_nearest_resource", {"lat": 1}, "out-1")["error"]
    rejected = tools.run_tool("submit_plan", {"summary": "s", "runs": [{"volunteer_id": "vol-9", "stops": []}]}, "out-1")  # repair can't fix
    assert rejected["problems"]
    assert tools.run_tool("find_nearest_resource", {"lat": 37.37, "lng": -121.80, "type": "pharmacy"}, "out-1")["resource_id"] == "pharm-1"


def test_greedy_covers_everyone_with_the_right_actions(world):
    plan = agent.greedy_plan("out-1", "timed out")
    actions = {s.resident_id: s.action for run in plan.runs for s in run.stops}
    assert actions == {"res-005": "door_knock", "res-001": "battery", "res-002": "cooler", "res-003": "ride"}
    assert plan.uncovered == [] and "did not finish: timed out" in plan.summary
    assert plan.runs[0].stops[0].reason.startswith("why ")


def test_greedy_overflow_becomes_the_next_wave(world):
    for i in range(6, 31):  # 25 more silent residents: 29 open cases >= 60, room for 18
        put(f"res-{i:03d}", "silent", 100 - i, "Critical" if 100 - i >= 80 else "High")
    plan = agent.greedy_plan("out-1")
    covered = [s.resident_id for run in plan.runs for s in run.stops]
    assert len(covered) == 18 and all(len(run.stops) <= 6 for run in plan.runs)
    assert len(plan.uncovered) == 11
    priority = {c["resident_id"]: c["priority"] for c in tools.list_open_cases("out-1")}
    assert max(priority[r] for r in plan.uncovered) <= min(priority[r] for r in covered)


def test_a_silent_case_is_covered_whatever_its_priority(world):
    put("res-039", "silent", 50, "Watch")  # §5: L3 means a door-knock in the next plan
    plan = agent.greedy_plan("out-1")
    assert {s.resident_id: s.action for r in plan.runs for s in r.stops}["res-039"] == "door_knock"
    with pytest.raises(tools.PlanError) as err:
        tools.submit_plan("out-1", [{"volunteer_id": "vol-1", "stops": [
            stop("res-005"), stop("res-001", "battery"), stop("res-002", "cooler"), stop("res-003", "ride")]}], "s")
    assert any("res-039" in p for p in err.value.problems)
