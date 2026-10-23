"""Deterministic, explainable triage score (0 to about 130) and priority bands.

The LLM extracts the inputs (Job 2); this code computes the score. No Bedrock here.

    device_weight   oxygen 40 | dialysis 35 | insulin 25 | power_wheelchair 15 | other 10  (max of devices)
    time_pressure   +30 if supply_hours_left < outage_hours_remaining
    alone           +10 if lives_alone
    silence         +5 per 30 virtual minutes without a reply (cap 25)
    distress        distress_level x 5
    transport       +5 if needs_transport
    status_ok       x 0.2 if assessment.status == "ok" and confidence >= 0.8

    Bands: Critical >= 80, High 60-79, Watch 30-59, OK < 30

Implements: PLAN.md §5 (triage scoring).
Owner: P2 (Backend and infra).
"""

from app.schemas import Assessment, Band, Resident, ScoreBreakdown

REVIEW_CONFIDENCE = 0.6  # below this, the case is flagged "Needs human review" (§4 Job 2)


def score(
    resident: Resident,
    assessment: Assessment | None,
    outage_hours_remaining: float,
    minutes_silent: float,
) -> ScoreBreakdown:
    """TODO(P2, §5): compute each part and the total."""
    ...


def band(total: float) -> Band:
    """TODO(P2, §5): map a score to Critical / High / Watch / OK."""
    ...
