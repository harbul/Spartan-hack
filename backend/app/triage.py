"""Deterministic, explainable triage score (0 to about 130) and priority bands.

The LLM extracts the inputs (Job 2); this code computes the score. No Bedrock here.

    device_weight   oxygen 40 | dialysis 35 | insulin 25 | power_wheelchair 15 | other 10  (max of devices)
    time_pressure   +30 if backup hours left < outage hours remaining
                    (backup = the reply's supply_hours_left, else baseline_backup_hours)
    alone           +10 if lives_alone
    silence         +5 per 30 virtual minutes without a reply (cap 25)
    distress        distress_level x 5
    transport       +5 if needs_transport
    status_ok       x 0.2 if assessment.status == "ok" and confidence >= 0.8

    Bands: Critical >= 80, High 60-79, Watch 30-59, OK < 30

Implements: PLAN.md §5 (triage scoring).
Owner: P2 (Backend and infra).
"""

import math

from app.schemas import Assessment, Band, Resident, ScoreBreakdown

REVIEW_CONFIDENCE = 0.6  # below this, the case is flagged "Needs human review" (§4 Job 2)
OK_CONFIDENCE = 0.8  # an "ok" reply only de-prioritizes at this confidence or higher

DEVICE_WEIGHT = {"oxygen": 40, "dialysis": 35, "insulin": 25, "power_wheelchair": 15, "other": 10}
SILENCE_STEP_MIN = 30
SILENCE_CAP = 25


def backup_hours_left(
    resident: Resident,
    assessment: Assessment | None,
    hours_since_outage_start: float,
    hours_since_reply: float,
) -> float:
    """Hours the resident's medicine or equipment still lasts at virtual now.

    Uses what the reply said (counted from the reply), else the registry's
    baseline (counted from the outage start).
    """
    if assessment and assessment.supply_hours_left is not None:
        return max(0.0, assessment.supply_hours_left - hours_since_reply)
    return max(0.0, resident.baseline_backup_hours - hours_since_outage_start)


def score(
    resident: Resident,
    assessment: Assessment | None,
    outage_hours_remaining: float,
    minutes_silent: float,
    backup_left: float,
) -> ScoreBreakdown:
    """Each §5 part and the total. `backup_left` comes from backup_hours_left()."""
    parts = {
        "device_weight": max((DEVICE_WEIGHT[d] for d in resident.devices), default=0),
        "time_pressure": 30 if backup_left < outage_hours_remaining else 0,
        "alone": 10 if resident.lives_alone else 0,
        "silence": min(SILENCE_CAP, 5 * math.floor(max(0.0, minutes_silent) / SILENCE_STEP_MIN)),
        "distress": 5 * assessment.distress_level if assessment else 0,
        "transport": 5 if assessment and assessment.needs_transport else 0,
    }
    ok = assessment is not None and assessment.status == "ok" and assessment.confidence >= OK_CONFIDENCE
    multiplier = 0.2 if ok else 1.0
    return ScoreBreakdown(
        **{k: float(v) for k, v in parts.items()},
        status_ok_multiplier=multiplier,
        total=round(sum(parts.values()) * multiplier, 1),
    )


def band(total: float) -> Band:
    if total >= 80:
        return "Critical"
    if total >= 60:
        return "High"
    if total >= 30:
        return "Watch"
    return "OK"
