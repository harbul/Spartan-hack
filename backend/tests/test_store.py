"""Tests for store.py and the routes built on it (/demo/reset, /outages), on fake tables.

Implements: PLAN.md §7 (data model), §8 (POST /demo/reset, POST /outages).
Owner: P2 (Backend and infra).
"""

import json
from decimal import Decimal

from fastapi.testclient import TestClient

from app import store
from app.main import app
from app.schemas import Trace

client = TestClient(app)
ZONE = json.loads((store.seed_dir() / "outage_zone.geojson").read_text())["features"][0]["geometry"]


def outage_body(polygon):
    return {
        "name": "East San Jose PSPS",
        "polygon": polygon,
        "starts_at": "2026-10-24T01:00:00Z",
        "est_restore_at": "2026-10-24T15:00:00Z",
    }


def test_reset_seeds_residents_and_config(tables):
    tables["CASES_TABLE"].put_item(Item={"outage_id": "old", "resident_id": "res-001"})
    assert client.post("/demo/reset").status_code == 200

    assert len(store.list_residents()) == 40
    assert tables["CASES_TABLE"].items == {}
    assert store.get_config("clock_offset_min") == 0
    assert [v["volunteer_id"] for v in store.get_config("volunteers")] == ["vol-1", "vol-2", "vol-3"]
    assert len(store.get_config("resources")) == 3


def test_outage_finds_every_resident_in_the_zone(tables):
    client.post("/demo/reset")
    body = client.post("/outages", json=outage_body(ZONE)).json()

    assert len(body["affected"]) == 40
    cases = store.list_cases(body["outage_id"])
    assert {c.status for c in cases} == {"not_contacted"}
    events = store.list_events(body["outage_id"])
    assert [e.type for e in events] == ["outage_started"]
    assert store.get_outage(body["outage_id"]).affected_ids == body["affected"]


def test_small_outage_finds_only_rosa(tables):
    client.post("/demo/reset")
    lat, lng = 37.3721, -121.8083  # Rosa Delgado, res-002
    d = 0.002
    square = {
        "type": "Polygon",
        "coordinates": [[[lng - d, lat - d], [lng + d, lat - d], [lng + d, lat + d], [lng - d, lat + d], [lng - d, lat - d]]],
    }
    assert client.post("/outages", json=outage_body(square)).json()["affected"] == ["res-002"]


def test_floats_round_trip_through_decimal(tables):
    trace = Trace(
        trace_id="t1", ts="2026-10-24T01:00:00Z", job="assess", model_id="m", input_masked="x",
        output={"confidence": 0.85, "supply_hours_left": 3}, latency_ms=1200, input_tokens=10, output_tokens=5,
    )
    store.put_trace(trace)
    stored = tables["TRACES_TABLE"].items[("t1",)]
    assert stored["output"]["confidence"] == Decimal("0.85")
    assert store.list_traces()[0] == trace


def test_missing_table_env_is_a_clear_503(monkeypatch):
    monkeypatch.delenv("RESIDENTS_TABLE", raising=False)
    response = client.post("/outages", json=outage_body(ZONE))
    assert response.status_code == 503
    assert "RESIDENTS_TABLE" in response.json()["detail"]
