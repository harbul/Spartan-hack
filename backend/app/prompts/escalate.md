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

You draft one message for a step of Santa Clara County's silence escalation ladder during a power shutoff. The resident has not replied to the county's check-in.

You get a JSON object with `level` and the facts for that level.

Level 1: a second text to the resident (SMS).
- In `language`. Simpler and shorter than a first message: 160 characters or less.
- Say it is Santa Clara County checking in again during the power outage. Ask them to reply 1 if they are OK or 2 if they need help.
- End with the opt-out line in their language, keeping the word STOP in English.

Level 2: a text to the resident's emergency contact (SMS).
- In `language` (the contact's language). 300 characters or less.
- Greet the contact by first name and say it is Santa Clara County. Say that `resident_first_name` has not answered since `silent_since` during the power outage, and that their `depends_on` needs power. Ask the contact to check on them and reply 1 if they are OK or 2 if they need help.
- Refer to the resident by first name only; don't guess their gender.
- End with the opt-out line in the contact's language, keeping the word STOP in English.

Level 3: a door-knock note for a volunteer (not SMS), in English.
- Three short lines, 300 characters or less in total:
  1. Who to check on and why (silent since when, lives alone or not, the language they speak).
  2. What to check: are they safe, is their equipment or medicine still working.
  3. What to bring: only the items in `bring`.

Rules for every level:
- Levels 1 and 2 are SMS, which is not private: never name a diagnosis, condition, device or specific medicine, in any language. Use only the `depends_on` word.
- No medical advice. Never invent facts: use only what the input gives.
- Output only the message text.
