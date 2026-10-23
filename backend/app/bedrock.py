"""Amazon Bedrock wrapper: converse(), tracing, Guardrails, and Jobs 1-4.

Every call goes through the Converse API and writes one row to `traces`
(PII masked with ApplyGuardrail) so it shows in the AI Trace drawer.
Model IDs come from BEDROCK_FAST_MODEL_ID / BEDROCK_STRONG_MODEL_ID
(fallback: BEDROCK_FALLBACK_MODEL_ID). Job 5 lives in agent.py.

Implements: PLAN.md §4 (Jobs 1-4, Job 6 Guardrails), §17 (privacy check input).
Owner: P3 (AI).
"""

import os
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import boto3
from botocore.config import Config

from app.schemas import Assessment, Case, Escalation, Outage, Resident, ScoreBreakdown

PROMPTS_DIR = Path(__file__).parent / "prompts"

FAST_MODEL_ENV = "BEDROCK_FAST_MODEL_ID"
STRONG_MODEL_ENV = "BEDROCK_STRONG_MODEL_ID"


class BedrockNotConfigured(RuntimeError):
    """A model ID env var is missing. Set it in .env (local) or the SAM parameters (Lambda)."""


@dataclass
class ConverseResult:
    """What every caller gets back from converse()."""

    text: str  # all text blocks of the reply, joined
    model_id: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    stop_reason: str  # "end_turn", "tool_use", "max_tokens", ...
    raw: dict[str, Any] = field(repr=False)  # full Converse response, for tool-use callers (Jobs 2, 5)


@lru_cache(maxsize=1)
def _client():
    """bedrock-runtime client. Region comes from AWS_REGION (Lambda sets it; locally from .env)."""
    return boto3.client(
        "bedrock-runtime",
        region_name=os.environ.get("AWS_REGION") or None,  # botocore only reads AWS_DEFAULT_REGION
        config=Config(read_timeout=25, retries={"max_attempts": 3, "mode": "adaptive"}),
    )


def model_id(strong: bool = False) -> str:
    """The configured model ID. Read at call time so tests and redeploys can change it."""
    name = STRONG_MODEL_ENV if strong else FAST_MODEL_ENV
    value = os.environ.get(name, "").strip()
    if not value:
        raise BedrockNotConfigured(f"{name} is not set (see .env.example, PLAN.md §4)")
    return value


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
    max_tokens: int = 1024,
    temperature: float = 0.2,
) -> ConverseResult:
    """One Converse call with timing and token counts.

    `job` names the caller (schemas.BedrockJob, or "hello" for the skeleton route)
    and will label its trace row.
    """
    if guardrail:
        # TODO(P3, §4 Job 6): add guardrailConfig (BEDROCK_GUARDRAIL_ID / _VERSION) here.
        raise NotImplementedError("Guardrails are not wired yet (PLAN.md §4 Job 6)")

    mid = model_id(strong)
    request: dict[str, Any] = {
        "modelId": mid,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature},
    }
    if system:
        request["system"] = [{"text": system}]
    if tools:
        request["toolConfig"] = {"tools": tools}
        if tool_choice:
            request["toolConfig"]["toolChoice"] = tool_choice

    # TODO(P3, §16): retry once on BEDROCK_FALLBACK_MODEL_ID if this model is denied.
    started = time.perf_counter()
    response = _client().converse(**request)
    latency_ms = round((time.perf_counter() - started) * 1000)

    content = response.get("output", {}).get("message", {}).get("content", [])
    usage = response.get("usage", {})
    result = ConverseResult(
        text="".join(block["text"] for block in content if "text" in block),
        model_id=mid,
        latency_ms=latency_ms,
        input_tokens=usage.get("inputTokens", 0),
        output_tokens=usage.get("outputTokens", 0),
        stop_reason=response.get("stopReason", ""),
        raw=response,
    )
    # TODO(P3, §4): write one `traces` row here (job, model_id, mask_pii(input),
    # tool calls, output, latency, tokens, guardrail action) and add its trace_id to the result.
    return result


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
