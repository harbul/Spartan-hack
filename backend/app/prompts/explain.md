<!--
Job 3 · Triage explainer · prompt spec + prompt.
Implements: PLAN.md §4 Job 3. Loaded by bedrock.explain_priority() (fast model).
Owner: P3 (AI).
Only the text under "## Prompt" is sent to the model (bedrock.load_prompt).
-->

# Job 3: Triage explainer

## Purpose
Write the one-line "why" the coordinator reads on each triage card.

## Inputs
- The score breakdown from §5 (`schemas.ScoreBreakdown`)
- The assessment from Job 2 (may be missing for silent residents)

## Output
- One sentence for Dana. Example: "Oxygen tank has ~3 h left but power is out for 14 h, he lives alone, and he wrote that he feels short of breath."

## Rules
- Explain the score; never change it or invent a factor that isn't in the breakdown
- Shown as AI-estimated urgency, never as a confirmed medical emergency (§9)

## Prompt

TODO(P3): write the system prompt.
