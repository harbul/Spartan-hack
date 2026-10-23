"""Unit tests for bedrock.py (converse, tracing, Jobs 1-2) with a stubbed bedrock-runtime client.

Implements: PLAN.md §4 (converse wrapper), §13 H0-H1.
Owner: P3 (AI).
"""

import json

import boto3
import pytest
from botocore.stub import ANY, Stubber
from eval_replies import privacy_violations  # tests/ is on sys.path under pytest

from app import bedrock, store
from app.schemas import Outage, Resident
from app.tools import RECORD_ASSESSMENT

FAST = "test.fast-model-v1:0"
STRONG = "test.strong-model-v1:0"


@pytest.fixture
def stub(monkeypatch):
    monkeypatch.setenv(bedrock.FAST_MODEL_ENV, FAST)
    monkeypatch.setenv(bedrock.STRONG_MODEL_ENV, STRONG)
    client = boto3.client(
        "bedrock-runtime",
        region_name="us-west-2",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    monkeypatch.setattr(bedrock, "_client", lambda: client)
    with Stubber(client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def reply(text: str) -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 12, "outputTokens": 7, "totalTokens": 19},
        "metrics": {"latencyMs": 300},
    }


MESSAGES = [{"role": "user", "content": [{"text": "hi"}]}]


def test_converse_uses_fast_model_and_returns_usage(stub):
    stub.add_response(
        "converse",
        reply("Hello, team."),
        {
            "modelId": FAST,
            "system": [{"text": "be brief"}],
            "messages": MESSAGES,
            "inferenceConfig": {"maxTokens": 1024, "temperature": 0.2},
        },
    )
    result = bedrock.converse("hello", "be brief", MESSAGES)
    assert result.text == "Hello, team."
    assert result.model_id == FAST
    assert (result.input_tokens, result.output_tokens) == (12, 7)
    assert result.stop_reason == "end_turn"
    assert result.latency_ms >= 0


def test_converse_strong_model(stub):
    stub.add_response(
        "converse",
        reply("ok"),
        {
            "modelId": STRONG,
            "messages": MESSAGES,
            "inferenceConfig": {"maxTokens": 1024, "temperature": 0.2},
        },
    )
    assert bedrock.converse("assess", "", MESSAGES, strong=True).model_id == STRONG


def test_missing_model_id_is_a_clear_error(monkeypatch):
    monkeypatch.delenv(bedrock.FAST_MODEL_ENV, raising=False)
    with pytest.raises(bedrock.BedrockNotConfigured, match=bedrock.FAST_MODEL_ENV):
        bedrock.converse("hello", "", MESSAGES)


# --- prompts, tracing ---------------------------------------------------------------


def test_load_prompt_sends_only_the_prompt_section():
    prompt = bedrock.load_prompt("assess")
    assert prompt.startswith("You read one resident's reply")
    assert "## Purpose" not in prompt and "<!--" not in prompt


def tool_reply(name: str, tool_input: dict) -> dict:
    return {
        "output": {
            "message": {
                "role": "assistant",
                "content": [{"toolUse": {"toolUseId": "tu-1", "name": name, "input": tool_input}}],
            }
        },
        "stopReason": "tool_use",
        "usage": {"inputTokens": 300, "outputTokens": 90, "totalTokens": 390},
        "metrics": {"latencyMs": 900},
    }


def test_converse_writes_a_masked_trace(stub, tables):
    stub.add_response("converse", reply("Hola Rosa"), None)
    messages = [{"role": "user", "content": [{"text": "phone +14085550102"}]}]
    result = bedrock.converse("checkin", "sys", messages)

    trace = tables["TRACES_TABLE"].items[(result.trace_id,)]
    assert trace["job"] == "checkin" and trace["model_id"] == FAST
    assert "+14085550102" not in trace["input_masked"] and "[phone]" in trace["input_masked"]
    assert trace["output"] == "Hola Rosa"


def test_hello_is_not_traced(stub, tables):
    stub.add_response("converse", reply("hi"), None)
    assert bedrock.converse("hello", "", MESSAGES).trace_id is None
    assert tables["TRACES_TABLE"].items == {}


def test_trace_failure_does_not_fail_the_call(stub, monkeypatch):
    monkeypatch.delenv("TRACES_TABLE", raising=False)  # store raises StoreNotConfigured
    stub.add_response("converse", reply("ok"), None)
    result = bedrock.converse("explain", "", MESSAGES)
    assert result.text == "ok" and result.trace_id is None


# --- Job 1: check-in writer -----------------------------------------------------------

RESIDENTS = {r["resident_id"]: Resident.model_validate(r) for r in store.load_seed("residents")}
OUTAGE = Outage(
    outage_id="out-1", name="East San Jose PSPS", polygon={}, starts_at="2026-10-24T01:00:00Z",
    est_restore_at="2026-10-24T15:00:00Z", affected_ids=[], status="active",
)


@pytest.fixture
def fake_converse(monkeypatch):
    calls = []

    def fake(job, system, messages, **kwargs):
        calls.append({"job": job, "system": system, "messages": messages, **kwargs})
        return bedrock.ConverseResult("Chào Minh, đây là Quận Santa Clara.", FAST, 10, 1, 1, "end_turn", {}, "tr-1")

    monkeypatch.setattr(bedrock, "converse", fake)
    return calls


def test_checkin_never_sends_device_words_to_the_model(fake_converse):
    for resident in RESIDENTS.values():
        bedrock.write_checkin(resident, OUTAGE)
    for call in fake_converse:
        assert privacy_violations(call["messages"][0]["content"][0]["text"]) == []


def test_checkin_facts_and_stop_line(fake_converse):
    result = bedrock.write_checkin(RESIDENTS["res-001"], OUTAGE)
    facts = json.loads(fake_converse[0]["messages"][0]["content"][0]["text"])
    assert facts == {
        "first_name": "Minh", "language": "Vietnamese", "depends_on": "equipment",
        "power_off": "6 PM", "power_back_estimate": "8 AM",
    }
    assert result.output.endswith("Reply STOP to opt out.") and result.trace_id == "tr-1"
    bedrock.write_checkin(RESIDENTS["res-002"], OUTAGE)  # Rosa: insulin only
    assert json.loads(fake_converse[1]["messages"][0]["content"][0]["text"])["depends_on"] == "medicine"


def test_checkins_run_for_everyone(fake_converse):
    results = bedrock.write_checkins(list(RESIDENTS.values()), OUTAGE)
    assert set(results) == set(RESIDENTS) and len(fake_converse) == 40


# --- Job 2: reply understanding -------------------------------------------------------

ASSESSMENT = {
    "status": "needs_help", "needs": ["power_for_device"], "supply_hours_left": 3,
    "needs_transport": False, "distress_level": 2, "detected_language": "vi",
    "english_translation": "The oxygen tank has about 3 hours left. I'm a bit short of breath.",
    "key_quote": "Bình oxy còn khoảng 3 tiếng", "confidence": 0.9, "reasoning": "Tank runs out before power returns.",
}
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 16


def test_assess_reply_forces_the_tool_and_sends_the_photo(stub, tables):
    stub.add_response(
        "converse",
        tool_reply("record_assessment", ASSESSMENT),
        {
            "modelId": STRONG,
            "system": [{"text": bedrock.load_prompt("assess")}],
            "messages": [{"role": "user", "content": [
                {"text": ANY},
                {"image": {"format": "png", "source": {"bytes": PNG}}},
            ]}],
            "inferenceConfig": {"maxTokens": 800, "temperature": 0},
            "toolConfig": {
                "tools": [RECORD_ASSESSMENT],
                "toolChoice": {"tool": {"name": "record_assessment"}},
            },
        },
    )
    result = bedrock.assess_reply(RESIDENTS["res-001"], "Chào Minh...", "Bình oxy còn khoảng 3 tiếng.", PNG)
    assert result.output.supply_hours_left == 3 and result.output.needs == ["power_for_device"]
    trace = tables["TRACES_TABLE"].items[(result.trace_id,)]
    assert trace["tool_calls"][0]["name"] == "record_assessment"
    assert "[image: png]" in trace["input_masked"]


def test_assess_reply_without_the_tool_call_is_an_error(stub):
    stub.add_response("converse", reply("I think they are fine"), None)
    with pytest.raises(ValueError, match="record_assessment"):
        bedrock.assess_reply(RESIDENTS["res-004"], "Hi Denise...", "all good")
