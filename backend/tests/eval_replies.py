"""AI eval: runs Job 2 (and the Job 1/4 privacy check) against data/test_replies.json.

Run by hand, not by pytest: `python tests/eval_replies.py` from backend/.
Pass at 18/20 or better on need type and priority band. Rerun after every
prompt change. Any device or diagnosis word in a resident message fails the run.

Implements: PLAN.md §17 (AI eval, privacy check).
Owner: P3 (AI).
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # run as a script from backend/

TEST_REPLIES = Path(__file__).resolve().parents[2] / "data" / "test_replies.json"
PASS_THRESHOLD = 18
OUTAGE_HOURS = 14  # replies arrive just after the 6 PM check-ins
HEROES = ["res-001", "res-002", "res-003", "res-004", "res-005"]

# Device and diagnosis words, EN/ES/VI, written without accents (matching ignores them).
PRIVACY_WORDS: list[str] = [
    # English
    "oxygen", "concentrator", "dialysis", "kidney", "insulin", "diabetes", "diabetic",
    "wheelchair", "ventilator", "cpap",
    # Spanish
    "oxigeno", "concentrador", "dialisis", "rinon", "insulina", "diabetico", "diabetica",
    "silla de ruedas", "respirador",
    # Vietnamese
    "oxy", "may tho", "loc than", "chay than", "than nhan tao", "tieu duong", "xe lan",
]


def _plain(text: str) -> str:
    """Lowercase, accents removed (Vietnamese đ -> d), so 'Oxígeno' and 'lọc thận' match."""
    text = text.lower().replace("đ", "d")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def privacy_violations(text: str) -> list[str]:
    """Return the privacy words found in a resident-facing message."""
    plain = _plain(text)
    return [w for w in PRIVACY_WORDS if re.search(rf"\b{re.escape(w)}\b", plain)]


def _residents():
    from app import store
    from app.schemas import Resident

    return {r["resident_id"]: Resident.model_validate(r) for r in store.load_seed("residents")}


def _demo_outage():
    from app.schemas import Outage

    return Outage(
        outage_id="eval", name="eval", polygon={}, starts_at="2026-10-24T01:00:00Z",
        est_restore_at="2026-10-24T15:00:00Z", affected_ids=[], status="active",
    )


def run_eval(path: Path = TEST_REPLIES) -> int:
    """Assess every labeled reply, compare need type and band, print a table, return the pass count."""
    from app import bedrock, triage

    residents = _residents()
    outage = _demo_outage()
    passed = 0
    print(f"{'reply':6} {'lang':4} {'need':5} {'band (want/got)':22} text")
    for reply in json.loads(path.read_text(encoding="utf-8"))["replies"]:
        resident = residents[reply["resident_id"]]
        image = None
        if reply["image"]:
            photo = path.parent / reply["image"]
            if photo.is_file():
                image = photo.read_bytes()
            else:
                print(f"  ! {reply['reply_id']}: {reply['image']} missing, assessing the text only")
        checkin = bedrock.write_checkin(resident, outage).output
        a = bedrock.assess_reply(resident, checkin, reply["text"], image).output
        got = triage.band(triage.score(resident, a, OUTAGE_HOURS, 0, triage.backup_hours_left(resident, a, 0, 0)).total)
        want = reply["expected"]
        need_ok = set(want["needs"]) & set(a.needs) if want["needs"] else not a.needs
        ok = bool(need_ok) and got == want["band"]
        passed += ok
        mark = "ok" if need_ok else "MISS"
        print(f"{reply['reply_id']:6} {reply['language']:4} {mark:5} {want['band'] + ' / ' + got:22} {reply['text'][:50]}")
    print(f"\n{passed}/20 passed (need {PASS_THRESHOLD})")
    return passed


def run_privacy_check() -> list[str]:
    """Job 1 for every resident and Job 4 L1/L2 for the heroes: device or diagnosis words fail."""
    from app import bedrock
    from app.schemas import Case

    residents = _residents()
    outage = _demo_outage()
    hits = []
    for rid, result in bedrock.write_checkins(list(residents.values()), outage).items():
        hits += [f"{rid} check-in: {w}" for w in privacy_violations(result.output)]
    for rid in HEROES:
        case = Case(outage_id="eval", resident_id=rid, status="awaiting_reply", priority=0, band="OK",
                    last_outbound_at=outage.starts_at)
        for level in (1, 2):
            text = bedrock.draft_escalation(residents[rid], case, level).output.text
            hits += [f"{rid} L{level}: {w}" for w in privacy_violations(text)]
    print("privacy check:", "no hits" if not hits else "\n  " + "\n  ".join(hits))
    return hits


if __name__ == "__main__":
    ok = run_eval() >= PASS_THRESHOLD
    ok = not run_privacy_check() and ok
    sys.exit(0 if ok else 1)
