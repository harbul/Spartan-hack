"""Silence escalation ladder and the virtual crisis clock.

Virtual now = real time + `config.clock_offset_min`. /clock/advance and the
1-minute EventBridge schedule both run the escalation check.

    L0  check-in sent
    L1  no reply after 30 min   Bedrock re-ping, simpler wording
    L2  no reply after 60 min   message to emergency contact; case -> escalated
    L3  no reply after 90 min   case -> silent; door-knock stop in the next plan
    Oxygen and dialysis use half the timers.

Implements: PLAN.md §5 (escalation ladder, incident timeline clock).
Owner: P2 (Backend and infra). Message text comes from bedrock.draft_escalation (P3).
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from app import bedrock, store, triage
from app.schemas import Case, Device, Escalation, Event, Message, Outage, Resident

LADDER_MINUTES = {1: 30, 2: 60, 3: 90}
STATUS_AT_LEVEL = {1: "awaiting_reply", 2: "escalated", 3: "silent"}
CHANNEL_AT_LEVEL = bedrock.CHANNELS
WHAT_AT_LEVEL = {1: "re-ping sent", 2: "emergency contact messaged", 3: "door-knock added"}
ESCALATING = {"awaiting_reply", "escalated"}
WORKERS = 8  # parallel residents per check; keeps a +3 h jump under the 30 s API limit


def iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def now() -> datetime:
    """Virtual now: real UTC time plus the stored clock offset."""
    return datetime.now(timezone.utc) + timedelta(minutes=store.get_config("clock_offset_min") or 0)


def advance(minutes: int) -> datetime:
    """Add to the clock offset and return the new virtual now. Forward only (MUST tier)."""
    if minutes <= 0:
        raise ValueError("the clock only moves forward")
    store.set_config("clock_offset_min", (store.get_config("clock_offset_min") or 0) + minutes)
    return now()


def timer_minutes(level: int, devices: list[Device]) -> float:
    """Minutes of silence before `level`, halved for oxygen and dialysis."""
    halved = bool({"oxygen", "dialysis"} & set(devices))
    return LADDER_MINUTES[level] / (2 if halved else 1)


def due_levels(case: Case, devices: list[Device], at: datetime) -> list[int]:
    """Ladder levels this case has reached but not yet taken."""
    if case.status not in ESCALATING or case.last_inbound_at or not case.last_outbound_at:
        return []
    silent_min = (at - triage.parse_ts(case.last_outbound_at)).total_seconds() / 60
    return [l for l in (1, 2, 3) if l > case.escalation_level and silent_min >= timer_minutes(l, devices)]


def _escalate(case: Case, resident: Resident, levels: list[int]) -> list[Escalation]:
    taken = []
    for level in levels:
        draft = bedrock.draft_escalation(resident, case, level)
        # Stamp each step when it fell due, so a big clock jump still lays the
        # timeline out correctly (and steps never share a message key).
        due = iso(triage.parse_ts(case.last_outbound_at) + timedelta(minutes=timer_minutes(level, resident.devices)))
        store.add_message(
            Message(
                resident_id=resident.resident_id,
                ts=due,
                direction="out",
                channel=CHANNEL_AT_LEVEL[level],
                text=draft.output.text,
                trace_id=draft.trace_id,
            )
        )
        before = case.status
        case.escalation_level = level
        case.status = STATUS_AT_LEVEL[level]
        store.put_case(case)
        store.add_event(
            Event(
                outage_id=case.outage_id,
                ts=due,
                type="escalation",
                label=f"{resident.name}: L{level} {WHAT_AT_LEVEL[level]}",
                resident_id=resident.resident_id,
                from_status=before,
                to_status=case.status,
            )
        )
        taken.append(draft.output)
    return taken


def run_escalation_check(outage_id: str) -> list[Escalation]:
    """Move every silent case up the ladder as needed and write `escalation` events."""
    at = now()
    residents = {r.resident_id: r for r in store.list_residents()}
    work = []
    for case in store.list_cases(outage_id):
        resident = residents[case.resident_id]
        if levels := due_levels(case, resident.devices, at):
            work.append((case, resident, levels))
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = pool.map(lambda item: _escalate(*item), work)
        return [e for taken in results for e in taken]


def rescore_case(
    case: Case, resident: Resident, outage: Outage, at: datetime, *, explain: bool | None = None, track: bool = True
) -> Event | None:
    """Recompute the score at `at`. Job 3 writes the "why" when `explain` is True,
    or when it is None and the band changed. Returns a `band_change` event if one
    was written (`track` False skips it, e.g. for the first score at check-in)."""
    breakdown, _ = triage.score_case(resident, case, outage, at)
    before = case.band
    case.priority = breakdown.total
    case.score_breakdown = breakdown
    case.band = triage.band(breakdown.total)
    changed = case.band != before
    if explain or (explain is None and changed):
        case.rationale = bedrock.explain_priority(breakdown, case.assessment, resident).output
    store.put_case(case)
    if not (track and changed):
        return None
    event = Event(
        outage_id=case.outage_id,
        ts=iso(at),
        type="band_change",
        label=f"{resident.name}: {before} → {case.band}",
        resident_id=resident.resident_id,
    )
    store.add_event(event)
    return event


def rescore_open_cases(outage_id: str) -> None:
    """Silence and backup countdowns change with time: rescore every open case."""
    at = now()
    outage = store.get_outage(outage_id)
    residents = {r.resident_id: r for r in store.list_residents()}
    open_cases = [c for c in store.list_cases(outage_id) if c.status not in ("not_contacted", "resolved")]
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(lambda c: rescore_case(c, residents[c.resident_id], outage, at), open_cases))
