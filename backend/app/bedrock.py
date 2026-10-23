"""Amazon Bedrock wrapper: converse(), tracing, Guardrails, and Jobs 1-4.

Every call goes through the Converse API and writes one row to `traces`
(PII masked) so it shows in the AI Trace drawer.
Model IDs come from BEDROCK_FAST_MODEL_ID / BEDROCK_STRONG_MODEL_ID
(fallback: BEDROCK_FALLBACK_MODEL_ID). Job 5 lives in agent.py.

Implements: PLAN.md §4 (Jobs 1-4, Job 6 Guardrails), §17 (privacy check input).
Owner: P3 (AI).
"""

import json
import logging
import os
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Generic, TypeVar, get_args
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import boto3
from botocore.config import Config

from app import store
from app.schemas import (
    Assessment,
    BedrockJob,
    Case,
    Escalation,
    Outage,
    Resident,
    ScoreBreakdown,
    ToolCall,
    Trace,
)
from app.tools import RECORD_ASSESSMENT

log = logging.getLogger(__name__)
T = TypeVar("T")

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
    trace_id: str | None = None  # None if the trace row couldn't be written


@dataclass
class JobResult(Generic[T]):
    """A job's output plus the trace row behind it (Message.trace_id, Plan.trace_id)."""

    output: T
    trace_id: str | None


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
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    _, sep, prompt = text.partition("\n## Prompt\n")
    if not sep or not prompt.strip():
        raise ValueError(f"prompts/{name}.md has no '## Prompt' section")
    return prompt.strip()


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
    """One Converse call with timing, token counts and a `traces` row.

    `job` names the caller (schemas.BedrockJob) and labels its trace row.
    Other names (the skeleton "hello") are not traced.
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
    result.trace_id = _record_trace(job, system, messages, result)
    return result


def _record_trace(
    job: str, system: str, messages: list[dict[str, Any]], result: ConverseResult
) -> str | None:
    """Write one `traces` row. A failed write never fails the Bedrock call itself."""
    if job not in get_args(BedrockJob):
        return None
    content = result.raw.get("output", {}).get("message", {}).get("content", [])
    tool_calls = [
        ToolCall(name=block["toolUse"]["name"], input=block["toolUse"]["input"])
        for block in content
        if "toolUse" in block
    ]
    trace = Trace(
        trace_id=uuid.uuid4().hex,
        ts=utc_now_iso(),
        job=job,
        model_id=result.model_id,
        input_masked=mask_pii(_render_input(system, messages)),
        tool_calls=tool_calls,
        output=result.text or (tool_calls[0].input if tool_calls else None),
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        guardrail_action=None,  # TODO(P3, §4 Job 6): from the response's guardrail trace
    )
    try:
        store.put_trace(trace)
    except Exception as err:  # noqa: BLE001  (traces are best effort; the job's result matters more)
        log.warning("trace not written for %s: %s", job, err)
        return None
    return trace.trace_id


def _render_input(system: str, messages: list[dict[str, Any]]) -> str:
    """Prompt as readable text for the Trace drawer. Images become a placeholder."""
    lines = [f"[system]\n{system}"] if system else []
    for message in messages:
        parts = []
        for block in message["content"]:
            if "text" in block:
                parts.append(block["text"])
            elif "image" in block:
                parts.append(f"[image: {block['image']['format']}]")
            else:
                parts.append(json.dumps(block, default=str, ensure_ascii=False))
        lines.append(f"[{message['role']}]\n" + "\n".join(parts))
    return "\n\n".join(lines)


_PHONE = re.compile(r"(?<!\w)(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")


def mask_pii(text: str) -> str:
    """Mask PII before storing traces. Phone numbers only for now.

    TODO(P3, §4 Job 6): names and addresses with ApplyGuardrail (BEDROCK_GUARDRAIL_ID).
    """
    return _PHONE.sub("[phone]", text)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# --- helpers shared by the jobs ---------------------------------------------------

LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "vi": "Vietnamese"}

try:
    PACIFIC = ZoneInfo("America/Los_Angeles")
except ZoneInfoNotFoundError:  # no tz database: PDT is right for the October demo
    PACIFIC = timezone(timedelta(hours=-7), "PDT")


def first_name(resident: Resident) -> str:
    """Given name. Vietnamese names put it last (Trần Văn Minh -> Minh)."""
    parts = resident.name.split()
    return parts[-1] if resident.language == "vi" else parts[0]


def local_time(ts: str) -> str:
    """ISO timestamp -> "6 PM" / "8:30 AM" in San Jose time."""
    t = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(PACIFIC)
    hour = t.hour % 12 or 12
    return f"{hour}{f':{t.minute:02d}' if t.minute else ''} {'AM' if t.hour < 12 else 'PM'}"


def _tool_input(result: ConverseResult, name: str) -> dict[str, Any]:
    for block in result.raw.get("output", {}).get("message", {}).get("content", []):
        if block.get("toolUse", {}).get("name") == name:
            return block["toolUse"]["input"]
    raise ValueError(f"model did not call {name} (stop reason: {result.stop_reason})")


def _image_format(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "png"
    if data[:3] == b"GIF":
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "jpeg"


# --- Job 1: check-in writer (fast model, parallel, ~10 threads) -------------


def write_checkin(resident: Resident, outage: Outage) -> JobResult[str]:
    """SMS of 300 chars or less in the resident's language. Never names a device or diagnosis.

    Privacy by construction: the model never sees the devices, only "medicine" or "equipment".
    """
    facts = {
        "first_name": first_name(resident),
        "language": LANGUAGE_NAMES[resident.language],
        "depends_on": "medicine" if set(resident.devices) == {"insulin"} else "equipment",
        "power_off": local_time(outage.starts_at),
        "power_back_estimate": local_time(outage.est_restore_at),
    }
    result = converse(
        "checkin",
        load_prompt("checkin"),
        [{"role": "user", "content": [{"text": json.dumps(facts, ensure_ascii=False)}]}],
        max_tokens=300,
        temperature=0.3,
    )
    text = result.text.strip().strip('"')
    if "STOP" not in text:  # the opt-out line is a hard rule, not a model preference
        text += " Reply STOP to opt out."
    return JobResult(text, result.trace_id)


def write_checkins(
    residents: list[Resident], outage: Outage, workers: int = 10
) -> dict[str, JobResult[str]]:
    """Job 1 for every resident in parallel. Keyed by resident_id."""
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(lambda r: write_checkin(r, outage), residents)
        return {r.resident_id: result for r, result in zip(residents, results)}


# --- Job 2: reply understanding (strong model, multimodal) ------------------


def assess_reply(
    resident: Resident, last_outbound: str, text: str, image_bytes: bytes | None = None
) -> JobResult[Assessment]:
    """Forced `record_assessment` tool call (spec in tools.RECORD_ASSESSMENT)."""
    facts = {
        "resident": {
            "first_name": first_name(resident),
            "age": resident.age,
            "language": LANGUAGE_NAMES[resident.language],
            "devices": resident.devices,
            "lives_alone": resident.lives_alone,
        },
        "last_message_sent": last_outbound,
        "reply_text": text,
    }
    content: list[dict[str, Any]] = [{"text": json.dumps(facts, ensure_ascii=False)}]
    if image_bytes:
        content.append({"image": {"format": _image_format(image_bytes), "source": {"bytes": image_bytes}}})
    result = converse(
        "assess",
        load_prompt("assess"),
        [{"role": "user", "content": content}],
        strong=True,
        tools=[RECORD_ASSESSMENT],
        tool_choice={"tool": {"name": "record_assessment"}},
        max_tokens=800,
        temperature=0,
    )
    return JobResult(Assessment.model_validate(_tool_input(result, "record_assessment")), result.trace_id)


# --- Job 3: triage explainer (fast model) -----------------------------------


def explain_priority(breakdown: ScoreBreakdown, assessment: Assessment | None) -> str:
    """One sentence for the coordinator explaining the score."""
    ...


# --- Job 4: escalation drafter (fast model) ---------------------------------


def draft_escalation(resident: Resident, case: Case, level: int) -> Escalation:
    """L1 simpler re-ping, L2 emergency-contact message, L3 door-knock note."""
    ...
