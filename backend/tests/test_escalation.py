"""Tests for the virtual clock, the silence escalation ladder and rescoring (no AWS).

Implements: PLAN.md §5 (escalation ladder, incident timeline clock).
Owner: P2 (Backend and infra).
"""

from datetime import datetime, timedelta, timezone

import pytest

from app import bedrock, escalation, store
from app.schemas import Case, Escalation, Outage

T0 = datetime(2026, 10, 24, 1, 0, tzinfo=timezone.utc)  # check-ins sent at 6 PM PDT
OUTAGE = Outage(
    outage_id="out-1", name="East San Jose PSPS", polygon={}, starts_at=escalation.iso(T0),
    est_restore_at=escalation.iso(T0 + timedelta(hours=14)), affected_ids=[], status="active",
)


@pytest.fixture
def world(tables, monkeypatch):
    """Seeded tables, an outage, Lupe (oxygen) and Rosa (insulin) awaiting a reply since T0."""
    store.reset_demo()
    store.put_outage(OUTAGE)
    for rid in ("res-005", "res-002"):
        store.put_case(Case(
            outage_id="out-1", resident_id=rid, status="awaiting_reply", priority=0, band="OK",
            last_outbound_at=escalation.iso(T0),
        ))
    drafts, explains = [], []

    def fake_draft(resident, case, level):
        drafts.append((resident.resident_id, level))
        channel = escalation.CHANNEL_AT_LEVEL[level]
        return bedrock.JobResult(Escalation(resident_id=resident.resident_id, level=level, channel=channel, text=f"L{level}"), "tr")

    def fake_explain(breakdown, assessment, resident):
        explains.append(breakdown.total)
        return bedrock.JobResult(f"why {breakdown.total}", "tr")

    monkeypatch.setattr(bedrock, "draft_escalation", fake_draft)
    monkeypatch.setattr(bedrock, "explain_priority", fake_explain)
    clock = {"now": T0}
    monkeypatch.setattr(escalation, "now", lambda: clock["now"])
    return {"clock": clock, "drafts": drafts, "explains": explains}


def at(world, minutes):
    world["clock"]["now"] = T0 + timedelta(minutes=minutes)


def case(rid):
    return next(c for c in store.list_cases("out-1") if c.resident_id == rid)


def test_timers_halve_for_oxygen_and_dialysis():
    assert escalation.timer_minutes(1, ["insulin"]) == 30
    assert escalation.timer_minutes(1, ["oxygen"]) == 15
    assert escalation.timer_minutes(3, ["dialysis", "other"]) == 45
    assert escalation.timer_minutes(3, ["power_wheelchair"]) == 90


def test_ladder_climbs_with_silence(world):
    at(world, 20)
    assert [(e.resident_id, e.level) for e in escalation.run_escalation_check("out-1")] == [("res-005", 1)]

    at(world, 50)  # Lupe passes L2 (30) and L3 (45); Rosa reaches L1 (30)
    taken = sorted((e.resident_id, e.level) for e in escalation.run_escalation_check("out-1"))
    assert taken == [("res-002", 1), ("res-005", 2), ("res-005", 3)]
    assert (case("res-005").status, case("res-005").escalation_level) == ("silent", 3)
    assert (case("res-002").status, case("res-002").escalation_level) == ("awaiting_reply", 1)

    lupe_messages = store.list_messages("res-005")
    assert [m.channel for m in lupe_messages] == ["sms", "contact", "door"]
    assert [m.ts for m in lupe_messages] == [escalation.iso(T0 + timedelta(minutes=m)) for m in (15, 30, 45)]
    assert case("res-005").last_outbound_at == escalation.iso(T0)  # the ladder never resets the clock

    at(world, 95)
    escalation.run_escalation_check("out-1")
    assert case("res-002").status == "silent"
    events = [e for e in store.list_events("out-1") if e.type == "escalation"]
    assert len(events) == 6 and events == sorted(events, key=lambda e: e.ts)


def test_check_is_idempotent(world):
    at(world, 60)
    assert escalation.run_escalation_check("out-1")
    assert escalation.run_escalation_check("out-1") == []


def test_a_resident_who_replied_never_escalates(world):
    rosa = case("res-002")
    rosa.status, rosa.last_inbound_at = "needs_help", escalation.iso(T0 + timedelta(minutes=10))
    store.put_case(rosa)
    at(world, 200)
    assert all(e.resident_id != "res-002" for e in escalation.run_escalation_check("out-1"))


def test_rescore_explains_only_band_changes(world):
    at(world, 150)
    escalation.rescore_open_cases("out-1")
    lupe = case("res-005")
    assert (lupe.priority, lupe.band) == (105, "Critical")  # 40 oxygen + 30 time + 10 alone + 25 silence
    assert lupe.rationale == "why 105.0"
    changes = [e for e in store.list_events("out-1") if e.type == "band_change"]
    assert {e.resident_id for e in changes} == {"res-005", "res-002"}

    explained = len(world["explains"])
    escalation.rescore_open_cases("out-1")  # same time, same bands: no new Job 3 calls
    assert len(world["explains"]) == explained


def test_clock_only_moves_forward(tables):
    store.set_config("clock_offset_min", 0)
    escalation.advance(30)
    escalation.advance(60)
    assert store.get_config("clock_offset_min") == 90
    with pytest.raises(ValueError):
        escalation.advance(0)


def test_escalated_case_gets_a_why_even_without_a_band_change(world):
    lupe = case("res-005")
    lupe.band, lupe.priority = "Critical", 80  # already Critical from her profile at check-in
    store.put_case(lupe)
    at(world, 50)
    escalation.run_escalation_check("out-1")
    escalation.rescore_open_cases("out-1")
    assert case("res-005").band == "Critical" and case("res-005").rationale
