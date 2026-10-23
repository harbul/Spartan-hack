"""Unit tests for the deterministic triage score: score and band for each hero resident.

Implements: PLAN.md §17 (test_triage.py), §5, §3 (hero residents).
Owner: P2 (Backend and infra).
"""

import json

import pytest

from app import store, triage
from app.schemas import Assessment, Resident

RESIDENTS = {r["resident_id"]: Resident.model_validate(r) for r in store.load_seed("residents")}
REPLIES = json.loads((store.seed_dir() / "test_replies.json").read_text())["replies"]
OUTAGE_HOURS = 14


def assessment(status="needs_help", needs=(), supply=None, transport=False, distress=0, confidence=0.9):
    return Assessment(
        status=status, needs=list(needs), supply_hours_left=supply, needs_transport=transport,
        distress_level=distress, detected_language="en", english_translation="", key_quote="",
        confidence=confidence, reasoning="",
    )


def at_reply(resident_id, a):
    """Score right after the 6 PM check-ins: 14 h left, no silence, nothing elapsed."""
    resident = RESIDENTS[resident_id]
    backup = triage.backup_hours_left(resident, a, 0, 0)
    return triage.score(resident, a, OUTAGE_HOURS, 0, backup)


@pytest.mark.parametrize(
    "resident_id, a, total, band",
    [
        ("res-001", assessment(needs=["power_for_device"], supply=3, distress=2), 90, "Critical"),  # Minh
        ("res-002", assessment(needs=["cooling_for_medication"], distress=1), 70, "High"),  # Rosa
        ("res-002", assessment(needs=["cooling_for_medication"], distress=0), 65, "High"),  # Rosa, calm
        ("res-003", assessment(needs=["transport"], transport=True, distress=1), 65, "High"),  # Harold
        ("res-004", assessment(status="ok"), 7, "OK"),  # Denise
    ],
)
def test_hero_replies(resident_id, a, total, band):
    breakdown = at_reply(resident_id, a)
    assert breakdown.total == total
    assert triage.band(breakdown.total) == band


def test_lupe_silent_for_150_minutes_is_critical():
    lupe = RESIDENTS["res-005"]
    elapsed_h = 2.5
    backup = triage.backup_hours_left(lupe, None, elapsed_h, 0)
    breakdown = triage.score(lupe, None, OUTAGE_HOURS - elapsed_h, 150, backup)
    assert (breakdown.silence, breakdown.time_pressure, breakdown.total) == (25, 30, 105)
    assert triage.band(breakdown.total) == "Critical"


def test_silence_steps_and_cap():
    lupe = RESIDENTS["res-005"]
    assert [triage.score(lupe, None, 14, m, 4).silence for m in (0, 29, 30, 89, 90, 600)] == [0, 0, 5, 10, 15, 25]


def test_low_confidence_ok_is_not_deprioritized():
    denise_unsure = at_reply("res-004", assessment(status="ok", confidence=0.7))
    assert denise_unsure.status_ok_multiplier == 1.0 and denise_unsure.total == 35


def test_backup_counts_down_from_the_right_moment():
    minh = RESIDENTS["res-001"]
    assert triage.backup_hours_left(minh, assessment(supply=3), 5, 1) == 2  # 3 h stated, 1 h ago
    assert triage.backup_hours_left(minh, None, 1.5, 0) == minh.baseline_backup_hours - 1.5
    assert triage.backup_hours_left(minh, assessment(supply=3), 10, 10) == 0  # never negative


@pytest.mark.parametrize("total, band", [(29.9, "OK"), (30, "Watch"), (59.9, "Watch"), (60, "High"), (79.9, "High"), (80, "Critical")])
def test_band_edges(total, band):
    assert triage.band(total) == band


@pytest.mark.parametrize("reply", REPLIES, ids=[r["reply_id"] for r in REPLIES])
def test_labeled_bands_match_the_score(reply):
    """data/test_replies.json labels must agree with the code that scores them."""
    e = reply["expected"]
    a = assessment(e["status"], e["needs"], e["supply_hours_left"], e["needs_transport"], e["distress_level"])
    assert triage.band(at_reply(reply["resident_id"], a).total) == e["band"]
