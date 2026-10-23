"""The H4-H6 golden path through the API, on fake tables with stand-in Bedrock jobs:
reset -> outage -> check-ins -> 4 hero replies -> (others reply) -> +3 h -> dashboard.

Implements: PLAN.md §13 H4-H6 gate ("replies flow into the queue and onto the map"), §17.
Owner: P2 (Backend and infra).
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app import bedrock, escalation, main, store
from app.main import app
from app.schemas import Assessment, Escalation

T0 = datetime(2026, 10, 24, 1, 0, tzinfo=timezone.utc)
ZONE = json.loads((store.seed_dir() / "outage_zone.geojson").read_text())["features"][0]["geometry"]
REPLIES = {r["resident_id"]: r for r in json.loads((store.seed_dir() / "test_replies.json").read_text())["replies"]}
OK = {"status": "ok", "needs": [], "supply_hours_left": None, "needs_transport": False, "distress_level": 0}
CROWD = {c["resident_id"]: {**c, "expected": {**OK, **c["expected"]}} for c in store.load_seed("crowd_replies")}
REPLIES.update(CROWD)  # the stand-in Job 2 reads a crowd reply as a confident OK
HEROES = ["res-001", "res-002", "res-003", "res-004"]
PHONES = {r["resident_id"]: r["phone"] for r in store.load_seed("residents")}
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 16
client = TestClient(app)


@pytest.fixture
def api(tables, monkeypatch):
    """Virtual clock starting at T0, stand-in Jobs 1-4, captured photo uploads."""
    monkeypatch.setattr(escalation, "now", lambda: T0 + timedelta(minutes=store.get_config("clock_offset_min") or 0))
    monkeypatch.setattr(bedrock, "write_checkins", lambda residents, outage: {
        r.resident_id: bedrock.JobResult(f"Hi {r.name}. Reply STOP to opt out.", "tr-checkin") for r in residents
    })

    def assess(resident, last_outbound, text, image=None):
        e = REPLIES[resident.resident_id]["expected"]
        return bedrock.JobResult(Assessment(
            status=e["status"], needs=e["needs"], supply_hours_left=e["supply_hours_left"],
            needs_transport=e["needs_transport"], distress_level=e["distress_level"],
            detected_language=REPLIES[resident.resident_id]["language"], english_translation=f"EN: {text}",
            key_quote=text, confidence=0.9, reasoning="",
        ), "tr-assess")

    monkeypatch.setattr(bedrock, "assess_reply", assess)
    monkeypatch.setattr(bedrock, "explain_priority", lambda b, a, r: bedrock.JobResult(f"{r.name}: {b.total}", "tr-explain"))
    monkeypatch.setattr(bedrock, "draft_escalation", lambda r, c, level: bedrock.JobResult(
        Escalation(resident_id=r.resident_id, level=level, channel=bedrock.CHANNELS[level], text=f"L{level}"), "tr-esc"))
    photos = {}
    monkeypatch.setattr(store, "put_photo", lambda key, data, content_type: photos.update({key: data}))
    return photos


def reply(resident_id, image=None):
    body = {"phone": PHONES[resident_id], "text": REPLIES[resident_id]["text"]}
    if image:
        body["image_b64"] = base64.b64encode(image).decode()
    response = client.post("/inbound", json=body)
    assert response.status_code == 200, response.text
    return response.json()["case"]


def by_id(dashboard):
    return {c["resident_id"]: c for c in dashboard["cases"]}


def test_golden_path_to_the_dashboard(api):
    assert client.post("/demo/reset").status_code == 200
    outage = client.post("/outages", json={
        "name": "East San Jose PSPS", "polygon": ZONE,
        "starts_at": escalation.iso(T0), "est_restore_at": escalation.iso(T0 + timedelta(hours=14)),
    }).json()
    assert len(outage["affected"]) == 40

    assert client.post(f"/outages/{outage['outage_id']}/checkins").json() == {"sent": 40}
    assert client.post(f"/outages/{outage['outage_id']}/checkins").json() == {"sent": 0}  # only once

    client.post("/clock/advance", json={"minutes": 10})
    minh = reply("res-001", image=PNG)
    assert (minh["status"], minh["band"], minh["priority"]) == ("needs_help", "Critical", 90)
    assert minh["rationale"] == "Trần Văn Minh: 90.0"
    assert list(api) == [f"replies/res-001/{escalation.iso(T0 + timedelta(minutes=10))}.png"]
    assert reply("res-002")["band"] == "High"
    assert reply("res-003")["band"] == "High"
    denise = reply("res-004")
    assert (denise["status"], denise["band"]) == ("ok", "OK")

    advanced = client.post("/clock/advance", json={"minutes": 180}).json()
    assert advanced["now"] == escalation.iso(T0 + timedelta(minutes=190))
    assert {e["resident_id"] for e in advanced["escalations"]} >= {"res-005"}

    dash = client.get("/dashboard").json()
    cases = by_id(dash)
    lupe = cases["res-005"]
    assert (lupe["status"], lupe["escalation_level"], lupe["band"]) == ("silent", 3, "Critical")
    assert lupe["rationale"] and lupe["backup_hours_left"] == 0.8  # 4 h baseline - 3 h 10 min
    assert cases["res-001"]["band"] == "Critical" and cases["res-004"]["status"] == "ok"
    assert dash["counts"] == {"safe": 1, "needs_help": 2, "critical": 1, "no_reply": 36}
    types = [e["type"] for e in dash["events"]]
    assert types[:2] == ["outage_started", "checkins_sent"] and types.count("reply") == 4
    assert dash["events"] == sorted(dash["events"], key=lambda e: e["ts"])
    assert len(dash["resources"]) == 3 and len(dash["volunteers"]) == 3

    thread = client.get("/residents/res-001/messages").json()["messages"]
    assert [(m["direction"], m["channel"]) for m in thread] == [("out", "sms"), ("in", "sms")]
    assert thread[1]["translation_en"].startswith("EN:") and thread[1]["image_key"].endswith(".png")
    assert [m["channel"] for m in client.get("/residents/res-005/messages").json()["messages"]] == ["sms", "sms", "contact", "door"]


def test_others_reply_leaves_only_four_silent(api):
    """With the "Others reply" step (phone simulator), silence is the signal again (§3)."""
    client.post("/demo/reset")
    outage = client.post("/outages", json={
        "name": "East San Jose PSPS", "polygon": ZONE,
        "starts_at": escalation.iso(T0), "est_restore_at": escalation.iso(T0 + timedelta(hours=14)),
    }).json()
    client.post(f"/outages/{outage['outage_id']}/checkins")
    client.post("/clock/advance", json={"minutes": 10})
    others = [rid for rid in REPLIES if rid not in HEROES]
    assert len(others) == 32
    for rid in HEROES + others:
        reply(rid)

    advanced = client.post("/clock/advance", json={"minutes": 180}).json()
    silent = {"res-005", "res-025", "res-036", "res-039"}
    assert {e["resident_id"] for e in advanced["escalations"]} == silent
    assert len(advanced["escalations"]) == 12  # L1-L3 for 4 residents: 12 Job 4 drafts, not ~108

    dash = client.get("/dashboard").json()
    cases = by_id(dash)
    assert {rid for rid, c in cases.items() if c["status"] == "silent"} == silent
    assert dash["counts"]["no_reply"] == 4
    assert cases["res-005"]["band"] == "Critical"
    assert sum(dash["counts"].values()) == 40
    assert [e["type"] for e in dash["events"]].count("reply") == 36


def test_unknown_phone_and_bad_input(api):
    client.post("/demo/reset")
    assert client.post("/inbound", json={"phone": "+15550000000", "text": "hi"}).status_code == 404
    assert client.post("/inbound", json={"phone": PHONES["res-001"], "text": "hi"}).status_code == 404  # no outage
    assert client.post("/clock/advance", json={"minutes": 0}).status_code == 422
    assert client.get("/dashboard").json()["outage"] is None


def test_scheduled_event_runs_the_check(api, monkeypatch):
    calls = []
    monkeypatch.setattr(store, "get_active_outage", lambda: type("O", (), {"outage_id": "out-x"})())
    monkeypatch.setattr(main, "_tick", lambda outage_id: calls.append(outage_id) or [])
    assert main.handler(dict(main.SCHEDULED_EVENT), None) == {"escalations": 0}
    assert calls == ["out-x"]
