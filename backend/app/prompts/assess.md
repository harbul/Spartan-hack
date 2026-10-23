<!--
Job 2 · Reply understanding · prompt spec + prompt.
Implements: PLAN.md §4 Job 2. Loaded by bedrock.assess_reply() (strong model, multimodal).
Owner: P3 (AI).
Only the text under "## Prompt" is sent to the model (bedrock.load_prompt).
-->

# Job 2: Reply understanding

## Purpose
Turn a messy resident reply (typos, Spanish, Vietnamese, a photo of a gauge) into structured needs.

## Inputs
- The resident profile
- The last outbound message
- The reply text, plus an optional image

## Output
- A forced tool call `record_assessment` (spec: `tools.RECORD_ASSESSMENT`, shape: `schemas.Assessment`):
  `status`, `needs[]`, `supply_hours_left`, `needs_transport`, `distress_level` (0-3),
  `detected_language`, `english_translation`, `key_quote` (verbatim, original language),
  `confidence` (0-1), `reasoning` (1-2 sentences)

## Rules
- Extract, never score: the triage score is computed in code (§5)
- `key_quote` is copied verbatim in the original language
- Use `supply_hours_left: null` when the reply doesn't say; never guess a number
- Be honest about `confidence`; below 0.6 the case goes to human review
- Evaluated by `tests/eval_replies.py` (pass at 18/20 or better)

## Prompt

TODO(P3): write the system prompt.
