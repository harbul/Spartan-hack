"""The AI eval script itself runs end to end (with stand-in jobs that answer as labeled).

Implements: PLAN.md §17 (AI eval, privacy check).
Owner: P3 (AI).
"""

import json

import eval_replies

from app import bedrock
from app.schemas import Assessment, Escalation

REPLIES = {r["text"]: r for r in json.loads(eval_replies.TEST_REPLIES.read_text())["replies"]}


def test_eval_and_privacy_check_run(monkeypatch, capsys):
    def assess(resident, last_outbound, text, image=None):
        e = REPLIES[text]["expected"]
        return bedrock.JobResult(Assessment(
            status=e["status"], needs=e["needs"], supply_hours_left=e["supply_hours_left"],
            needs_transport=e["needs_transport"], distress_level=e["distress_level"], detected_language="x",
            english_translation="", key_quote=text, confidence=0.9, reasoning="",
        ), None)

    monkeypatch.setattr(bedrock, "assess_reply", assess)
    monkeypatch.setattr(bedrock, "write_checkin", lambda r, o: bedrock.JobResult("Hi. Reply STOP", None))
    monkeypatch.setattr(bedrock, "write_checkins", lambda rs, o: {r.resident_id: bedrock.JobResult("Hola", None) for r in rs})
    monkeypatch.setattr(bedrock, "draft_escalation", lambda r, c, level: bedrock.JobResult(
        Escalation(resident_id=r.resident_id, level=level, channel="sms", text="su oxígeno" if level == 2 else "ok"), None))

    assert eval_replies.run_eval() == 20
    hits = eval_replies.run_privacy_check()
    assert len(hits) == 5 and all("L2: oxigeno" in h for h in hits)  # the planted word is caught
    assert "20/20 passed" in capsys.readouterr().out
