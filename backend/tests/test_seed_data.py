"""Checks on data/: every record matches the shared contract and the demo story holds.

Implements: PLAN.md §3 (demo scenario), §7 (records), §17 (eval inputs).
Owner: P4 (Story, data and video), run by P2's pytest.
"""

import json

from app import geo, store
from app.schemas import Resident, Resource, Volunteer

ZONE = json.loads((store.seed_dir() / "outage_zone.geojson").read_text())["features"][0]["geometry"]
RESIDENTS = [Resident.model_validate(r) for r in store.load_seed("residents")]
REPLIES = json.loads((store.seed_dir() / "test_replies.json").read_text())["replies"]
CROWD = store.load_seed("crowd_replies")
VOLUNTEERS = [Volunteer.model_validate(v) for v in store.load_seed("volunteers")]
MAX_STOPS_PER_VOLUNTEER = 6  # §4 Job 5 system prompt


def test_residents_are_valid_unique_and_in_the_zone():
    assert len(RESIDENTS) == 40
    assert len({r.resident_id for r in RESIDENTS}) == 40
    phones = [r.phone for r in RESIDENTS] + [r.emergency_contact.phone for r in RESIDENTS]
    assert len(set(phones)) == len(phones)
    assert all(p.startswith("+1408555") for p in phones)  # fictional 555 numbers only
    assert all(geo.point_in_polygon(r.lat, r.lng, ZONE) for r in RESIDENTS)


def test_hero_residents():
    heroes = {r.resident_id: r for r in RESIDENTS[:5]}
    assert [r.name for r in heroes.values()] == [
        "Trần Văn Minh", "Rosa Delgado", "Harold Kim", "Denise Okafor", "Lupe Ramírez",
    ]
    assert heroes["res-005"].lives_alone and heroes["res-005"].language == "es"


def test_resources_and_volunteers_are_valid():
    resources = [Resource.model_validate(r) for r in store.load_seed("resources")]
    assert sorted(r.type for r in resources) == ["pharmacy", "resource_center", "resource_center"]
    assert not any(geo.point_in_polygon(r.lat, r.lng, ZONE) for r in resources)  # they have power
    assert len(VOLUNTEERS) == 3
    assert not any(geo.point_in_polygon(v.start.lat, v.start.lng, ZONE) for v in VOLUNTEERS)  # they drive in


def test_test_replies_match_their_residents():
    by_id = {r.resident_id: r for r in RESIDENTS}
    assert len(REPLIES) == 20
    assert {r["language"] for r in REPLIES} == {"en", "es", "vi"}
    assert sum(1 for r in REPLIES if r["image"]) == 2
    assert "res-005" not in {r["resident_id"] for r in REPLIES}  # Lupe never replies
    for reply in REPLIES:
        assert by_id[reply["resident_id"]].language == reply["language"], reply["reply_id"]
        assert reply["expected"]["band"] in {"Critical", "High", "Watch", "OK"}


def test_crowd_replies_leave_only_lupe_and_three_others_silent():
    by_id = {r.resident_id: r for r in RESIDENTS}
    crowd_ids = [c["resident_id"] for c in CROWD]
    assert len(crowd_ids) == len(set(crowd_ids)) == 16
    assert not set(crowd_ids) & {r["resident_id"] for r in REPLIES}  # one reply per resident
    for c in CROWD:
        assert by_id[c["resident_id"]].language == c["language"], c["resident_id"]
        assert c["expected"] == {"status": "ok", "band": "OK"}
    replied = set(crowd_ids) | {r["resident_id"] for r in REPLIES}
    silent = {r.resident_id for r in RESIDENTS} - replied
    assert silent == {"res-005", "res-025", "res-036", "res-039"}  # matches frontend/src/api/mock.ts


def test_golden_path_stops_fit_the_volunteers():
    """Every High/Critical reply and every silent door-knock fits in one plan (§4 Job 5)."""
    needs_stop = [r for r in REPLIES if r["expected"]["status"] == "needs_help" and r["expected"]["band"] in {"High", "Critical"}]
    replied = {c["resident_id"] for c in CROWD} | {r["resident_id"] for r in REPLIES}
    door_knocks = [r for r in RESIDENTS if r.resident_id not in replied]
    assert len(needs_stop) + len(door_knocks) <= len(VOLUNTEERS) * MAX_STOPS_PER_VOLUNTEER
