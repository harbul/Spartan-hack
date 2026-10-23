"""Unit tests for bedrock.converse() against a stubbed bedrock-runtime client (no AWS calls).

Implements: PLAN.md §4 (converse wrapper), §13 H0-H1.
Owner: P3 (AI).
"""

import boto3
import pytest
from botocore.stub import Stubber

from app import bedrock

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
