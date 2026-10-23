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

from datetime import datetime

from app.schemas import Device, Escalation

LADDER_MINUTES = {1: 30, 2: 60, 3: 90}


def now() -> datetime:
    """Virtual now: real UTC time plus the stored clock offset."""
    ...


def advance(minutes: int) -> datetime:
    """Add to the clock offset and return the new virtual now."""
    ...


def timer_minutes(level: int, devices: list[Device]) -> float:
    """Minutes of silence before `level`, halved for oxygen and dialysis."""
    ...


def run_escalation_check(outage_id: str) -> list[Escalation]:
    """Move every silent case up the ladder as needed and write `escalation` events."""
    ...
