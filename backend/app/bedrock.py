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

# Job 6, Guardrails (§4). Two guardrails, both optional until H0 (unset = skipped):
#   advice  denied topic "medical advice": on every resident-facing SMS (Jobs 1, 4) and to screen replies
#   pii     names, addresses, phones anonymized: only for trace rows, through ApplyGuardrail
# One guardrail can't do both: PII filters on the SMS jobs would also mask "Hi Rosa".
GUARDRAIL_ENV = "BEDROCK_GUARDRAIL_ID"
GUARDRAIL_VERSION_ENV = "BEDROCK_GUARDRAIL_VERSION"
PII_GUARDRAIL_ENV = "BEDROCK_PII_GUARDRAIL_ID"
PII_GUARDRAIL_VERSION_ENV = "BEDROCK_PII_GUARDRAIL_VERSION"


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
    guardrail_action: str | None = None  # "NONE" or "INTERVENED" when the advice guardrail ran; None if it didn't

    @property
    def blocked(self) -> bool:
        return self.guardrail_action == "INTERVENED"


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


def guardrail_config(id_env: str, version_env: str) -> tuple[str, str] | None:
    """(id, version) of a configured guardrail, or None while it isn't set up (offline, before H0)."""
    guardrail_id = os.environ.get(id_env, "").strip()
    if not guardrail_id:
        return None
    return guardrail_id, os.environ.get(version_env, "").strip() or "DRAFT"


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
    `guardrail` runs the advice guardrail on the call, when one is configured.
    """
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
    advice = guardrail_config(GUARDRAIL_ENV, GUARDRAIL_VERSION_ENV) if guardrail else None
    if advice:
        request["guardrailConfig"] = {"guardrailIdentifier": advice[0], "guardrailVersion": advice[1], "trace": "enabled"}

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
    if advice:
        result.guardrail_action = "INTERVENED" if result.stop_reason == "guardrail_intervened" else "NONE"
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
        guardrail_action=result.guardrail_action,
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
    """Mask PII before storing traces: names, addresses and phones with the PII guardrail
    (ApplyGuardrail) when it is configured, then phone numbers by pattern either way."""
    pii = guardrail_config(PII_GUARDRAIL_ENV, PII_GUARDRAIL_VERSION_ENV)
    if pii:
        try:
            response = _client().apply_guardrail(
                guardrailIdentifier=pii[0], guardrailVersion=pii[1], source="OUTPUT", content=[{"text": {"text": text}}]
            )
            if response.get("action") == "GUARDRAIL_INTERVENED" and response.get("outputs"):
                text = "".join(o.get("text", "") for o in response["outputs"])
        except Exception as err:  # noqa: BLE001  (masking falls back to the pattern; the trace still gets written)
            log.warning("PII guardrail failed, masking phones only: %s", err)
    return _PHONE.sub("[phone]", text)


def screen_reply(text: str) -> JobResult[bool] | None:
    """Check a resident's reply against the advice guardrail (ApplyGuardrail, source INPUT).

    True means it asks for medical advice (dosing, skipping treatment, equipment settings):
    the app never answers that, so the case goes to a person (needs_review). Job 2 still
    assesses the reply. None while no guardrail is configured. Traced as job "guardrail".
    """
    advice = guardrail_config(GUARDRAIL_ENV, GUARDRAIL_VERSION_ENV)
    if not advice:
        return None
    started = time.perf_counter()
    response = _client().apply_guardrail(
        guardrailIdentifier=advice[0], guardrailVersion=advice[1], source="INPUT", content=[{"text": {"text": text}}]
    )
    latency_ms = round((time.perf_counter() - started) * 1000)
    intervened = response.get("action") == "GUARDRAIL_INTERVENED"
    topics = [
        topic["name"]
        for assessment in response.get("assessments", [])
        for topic in assessment.get("topicPolicy", {}).get("topics", [])
    ]
    trace = Trace(
        trace_id=uuid.uuid4().hex,
        ts=utc_now_iso(),
        job="guardrail",
        model_id=f"guardrail:{advice[0]}:{advice[1]}",
        input_masked=mask_pii(text),
        output={"blocked_topics": topics} if intervened else "No denied topic",
        latency_ms=latency_ms,
        input_tokens=0,
        output_tokens=0,
        guardrail_action="INTERVENED" if intervened else "NONE",
    )
    try:
        store.put_trace(trace)
        trace_id: str | None = trace.trace_id
    except Exception as err:  # noqa: BLE001  (same as converse traces: best effort)
        log.warning("guardrail trace not written: %s", err)
        trace_id = None
    return JobResult(intervened, trace_id)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


# --- helpers shared by the jobs ---------------------------------------------------

LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "vi": "Vietnamese"}

try:
    PACIFIC = ZoneInfo("America/Los_Angeles")
except ZoneInfoNotFoundError:  # no tz database: PDT is right for the October demo
    PACIFIC = timezone(timedelta(hours=-7), "PDT")


def depends_on(resident: Resident) -> str:
    """The only word SMS jobs get about a resident's devices (privacy, §4 Job 1)."""
    return "medicine" if set(resident.devices) == {"insulin"} else "equipment"


def with_stop_line(text: str) -> str:
    """Every resident-facing SMS carries the opt-out; a hard rule, not a model preference."""
    text = text.strip().strip('"')
    return text if "STOP" in text else f"{text} Reply STOP to opt out."


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


def image_format(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return "png"
    if data[:3] == b"GIF":
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return "jpeg"


# --- Job 1: check-in writer (fast model, parallel, ~10 threads) -------------

# Fixed texts if the advice guardrail blocks a drafted SMS: the resident still gets a safe message.
SAFE_CHECKIN = {
    "en": "Hi {first_name}, this is Santa Clara County. Power in your area is off from {power_off} until about "
    "{power_back_estimate}. How many hours can your {depends_on} last without power? Reply 1 if you're OK, 2 if you need help.",
    "es": "Hola {first_name}, le escribe el Condado de Santa Clara. La luz en su zona se corta de {power_off} hasta "
    "aproximadamente {power_back_estimate}. ¿Cuántas horas puede durar su {depends_on} sin luz? Responda 1 si está bien, "
    "2 si necesita ayuda.",
    "vi": "Chào {first_name}, đây là Quận Santa Clara. Khu vực của bạn mất điện từ {power_off} đến khoảng "
    "{power_back_estimate}. Khi không có điện, {depends_on} của bạn dùng được bao nhiêu giờ? Trả lời 1 nếu ổn, 2 nếu cần giúp.",
}
# depends_on() is "medicine" or "equipment"; the fixed texts need it in the resident's language.
DEPENDS_ON_WORD = {
    "en": {"medicine": "medicine", "equipment": "equipment"},
    "es": {"medicine": "medicina", "equipment": "equipo"},
    "vi": {"medicine": "thuốc", "equipment": "thiết bị"},
}
SAFE_REPING = {
    "en": "Hi {first_name}, Santa Clara County checking on you during the power outage. Please reply 1 if you're OK or 2 if you need help.",
    "es": "Hola {first_name}, el Condado de Santa Clara quiere saber cómo está durante el apagón. Responda 1 si está bien o 2 si necesita ayuda.",
    "vi": "Chào {first_name}, Quận Santa Clara hỏi thăm bạn trong lúc mất điện. Trả lời 1 nếu ổn hoặc 2 nếu cần giúp.",
}
SAFE_CONTACT = {
    "en": "Hi {contact_first_name}, Santa Clara County here. We have not heard from {resident_first_name} since "
    "{silent_since} during the power outage. If you can, please check on them or call us.",
    "es": "Hola {contact_first_name}, le escribe el Condado de Santa Clara. No sabemos de {resident_first_name} desde "
    "las {silent_since} durante el apagón. Si puede, por favor vea cómo está o llámenos.",
    "vi": "Chào {contact_first_name}, đây là Quận Santa Clara. Chúng tôi chưa nghe tin từ {resident_first_name} từ "
    "{silent_since} trong lúc mất điện. Nếu được, xin hãy kiểm tra hoặc gọi cho chúng tôi.",
}


def write_checkin(resident: Resident, outage: Outage) -> JobResult[str]:
    """SMS of 300 chars or less in the resident's language. Never names a device or diagnosis.

    Privacy by construction: the model never sees the devices, only "medicine" or "equipment".
    """
    facts = {
        "first_name": first_name(resident),
        "language": LANGUAGE_NAMES[resident.language],
        "depends_on": depends_on(resident),
        "power_off": local_time(outage.starts_at),
        "power_back_estimate": local_time(outage.est_restore_at),
    }
    result = converse(
        "checkin",
        load_prompt("checkin"),
        [{"role": "user", "content": [{"text": json.dumps(facts, ensure_ascii=False)}]}],
        max_tokens=300,
        temperature=0.3,
        guardrail=True,
    )
    if result.blocked:
        word = DEPENDS_ON_WORD[resident.language][facts["depends_on"]]
        text = SAFE_CHECKIN[resident.language].format(**{**facts, "depends_on": word})
    else:
        text = result.text
    return JobResult(with_stop_line(text), result.trace_id)


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
        content.append({"image": {"format": image_format(image_bytes), "source": {"bytes": image_bytes}}})
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


def explain_priority(
    breakdown: ScoreBreakdown, assessment: Assessment | None, resident: Resident
) -> JobResult[str]:
    """One sentence for the coordinator explaining the score. Dashboard only, so it may name devices."""
    parts = breakdown.model_dump(exclude={"total", "status_ok_multiplier"})
    facts = {
        "resident": {
            "first_name": first_name(resident),
            "age": resident.age,
            "devices": resident.devices,
            "lives_alone": resident.lives_alone,
            "baseline_backup_hours": resident.baseline_backup_hours,
        },
        "score_parts": {k: v for k, v in parts.items() if v},
        "said_they_are_ok": breakdown.status_ok_multiplier < 1,
        "reply": None
        if assessment is None
        else {
            "english_translation": assessment.english_translation,
            "needs": assessment.needs,
            "supply_hours_left": assessment.supply_hours_left,
            "needs_transport": assessment.needs_transport,
            "distress_level": assessment.distress_level,
        },
    }
    result = converse(
        "explain",
        load_prompt("explain"),
        [{"role": "user", "content": [{"text": json.dumps(facts, ensure_ascii=False)}]}],
        max_tokens=120,
        temperature=0.2,
    )
    return JobResult(result.text.strip().strip('"'), result.trace_id)


# --- Job 4: escalation drafter (fast model) ---------------------------------


CHANNELS = {1: "sms", 2: "contact", 3: "door"}


def _bring(resident: Resident) -> list[str]:
    """What a door-knock volunteer brings, decided in code so the model can't invent kit."""
    items = ["printed resource center info", "phone to call 911 if they are in danger"]
    if "insulin" in resident.devices:
        items.insert(0, "cooler with ice")
    if set(resident.devices) - {"insulin"}:
        items.insert(0, "charged battery pack")
    return items


def draft_escalation(resident: Resident, case: Case, level: int) -> JobResult[Escalation]:
    """L1 simpler re-ping, L2 emergency-contact message, L3 door-knock note.

    L1 and L2 are SMS: like Job 1, the model never sees the devices.
    """
    silent_since = local_time(case.last_outbound_at) if case.last_outbound_at else "this evening"
    contact = resident.emergency_contact
    if level == 1:
        facts = {
            "level": 1,
            "first_name": first_name(resident),
            "language": LANGUAGE_NAMES[resident.language],
        }
    elif level == 2:
        facts = {
            "level": 2,
            "contact_first_name": contact.name.split()[-1] if contact.language == "vi" else contact.name.split()[0],
            "language": LANGUAGE_NAMES[contact.language],
            "resident_first_name": first_name(resident),
            "silent_since": silent_since,
            "depends_on": depends_on(resident),
        }
    else:
        facts = {
            "level": 3,
            "first_name": first_name(resident),
            "age": resident.age,
            "devices": resident.devices,
            "lives_alone": resident.lives_alone,
            "speaks": LANGUAGE_NAMES[resident.language],
            "silent_since": silent_since,
            "emergency_contact": f"{contact.name} ({contact.relation}), already texted",
            "bring": _bring(resident),
        }
    result = converse(
        "escalate",
        load_prompt("escalate"),
        [{"role": "user", "content": [{"text": json.dumps(facts, ensure_ascii=False)}]}],
        max_tokens=300,
        temperature=0.3,
        guardrail=level < 3,  # L1 and L2 are SMS; L3 is a note for our own volunteer
    )
    text = result.text
    if result.blocked and level < 3:
        language = resident.language if level == 1 else contact.language
        text = (SAFE_REPING if level == 1 else SAFE_CONTACT)[language].format(**facts)
    text = with_stop_line(text) if level < 3 else text.strip()
    escalation = Escalation(resident_id=resident.resident_id, level=level, channel=CHANNELS[level], text=text)
    return JobResult(escalation, result.trace_id)
