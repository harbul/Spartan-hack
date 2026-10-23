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
    assert len([Volunteer.model_validate(v) for v in store.load_seed("volunteers")]) == 3


def test_test_replies_match_their_residents():
    by_id = {r.resident_id: r for r in RESIDENTS}
    assert len(REPLIES) == 20
    assert {r["language"] for r in REPLIES} == {"en", "es", "vi"}
    assert sum(1 for r in REPLIES if r["image"]) == 2
    assert "res-005" not in {r["resident_id"] for r in REPLIES}  # Lupe never replies
    for reply in REPLIES:
        assert by_id[reply["resident_id"]].language == reply["language"], reply["reply_id"]
        assert reply["expected"]["band"] in {"Critical", "High", "Watch", "OK"}
