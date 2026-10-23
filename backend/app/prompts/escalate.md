<!--
Job 4 · Escalation drafter · prompt spec + prompt.
Implements: PLAN.md §4 Job 4, §5 escalation ladder. Loaded by bedrock.draft_escalation() (fast model).
Owner: P3 (AI).
Only the text under "## Prompt" is sent to the model (bedrock.load_prompt).
-->

# Job 4: Escalation drafter

## Purpose
Draft the message for each step of the silence escalation ladder.

## Inputs
- The resident profile (incl. emergency contact and their language)
- The case and the escalation level (1, 2 or 3)
- Outage window

## Output
- **Level 1:** a simpler re-ping to the resident, in the resident's language
- **Level 2:** a message to the emergency contact, in the contact's language
- **Level 3:** a door-knock note for the volunteer: what to check and what to bring

## Rules
- Levels 1 and 2 are SMS: never name a diagnosis or a specific device (privacy check, §17)
- No medical advice; never invent facts
- Level 3 is for the volunteer's route sheet, not SMS, so it may say what to bring

## Prompt

TODO(P3): write the system prompt.
