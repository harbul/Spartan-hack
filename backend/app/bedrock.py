"""Amazon Bedrock wrapper: converse(), tracing, Guardrails, and Jobs 1-4.

Every call goes through the Converse API and writes one row to `traces`
(PII masked with ApplyGuardrail) so it shows in the AI Trace drawer.
Model IDs come from BEDROCK_FAST_MODEL_ID / BEDROCK_STRONG_MODEL_ID
(fallback: BEDROCK_FALLBACK_MODEL_ID). Job 5 lives in agent.py.

Implements: PLAN.md §4 (Jobs 1-4, Job 6 Guardrails), §17 (privacy check input).
Owner: P3 (AI).
"""

from pathlib import Path
from typing import Any

from app.schemas import Assessment, Case, Escalation, Outage, Resident, ScoreBreakdown

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Return the text under the `## Prompt` heading of prompts/<name>.md.

    The spec above that heading is for humans and is not sent to the model.
    """
    ...


def converse(
    job: str,
    system: str,
    messages: list[dict[str, Any]],
    *,
    strong: bool = False,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: dict[str, Any] | None = None,
    guardrail: bool = False,
) -> dict[str, Any]:
    """One Converse call with timing, token counts and a trace row. Returns the raw response."""
    ...


def mask_pii(text: str) -> str:
    """Mask names, phone numbers and addresses with ApplyGuardrail before storing traces."""
    ...


# --- Job 1: check-in writer (fast model, parallel, ~10 threads) -------------


def write_checkin(resident: Resident, outage: Outage) -> str:
    """SMS of 300 chars or less in the resident's language. Never names a device or diagnosis."""
    ...


# --- Job 2: reply understanding (strong model, multimodal) ------------------


def assess_reply(
    resident: Resident, last_outbound: str, text: str, image_bytes: bytes | None = None
) -> Assessment:
    """Forced `record_assessment` tool call (spec in tools.RECORD_ASSESSMENT)."""
    ...


# --- Job 3: triage explainer (fast model) -----------------------------------


def explain_priority(breakdown: ScoreBreakdown, assessment: Assessment | None) -> str:
    """One sentence for the coordinator explaining the score."""
    ...


# --- Job 4: escalation drafter (fast model) ---------------------------------


def draft_escalation(resident: Resident, case: Case, level: int) -> Escalation:
    """L1 simpler re-ping, L2 emergency-contact message, L3 door-knock note."""
    ...
