<!--
Job 1 · Check-in writer · prompt spec + prompt.
Implements: PLAN.md §4 Job 1. Loaded by bedrock.write_checkin() (fast model).
Owner: P3 (AI).
Only the text under "## Prompt" is sent to the model (bedrock.load_prompt).
-->

# Job 1: Check-in writer

## Purpose
Write each affected resident a short, personal check-in SMS in their language.

## Inputs
- Resident profile: first name, language (`en` / `es` / `vi`), devices, baseline backup hours
- Outage start and estimated restore time

## Output
- One SMS, 300 characters or less, in the resident's language, plain reading level
- Asks two things: how many hours their medical equipment or medicine can last without power, and whether they need help (reply 1 if OK, 2 if they need help)
- Example: "Hi Rosa, this is Santa Clara County. Power in your area goes off at 6 PM until about 8 AM. How many hours can your medical equipment or medicine last without power? Reply 1 if you're OK, 2 if you need help."

## Rules
- No medical advice; never invent facts
- **Never name a diagnosis or a specific device.** The device only picks the wording ("equipment" vs "medicine"). SMS is not private.
- Always include "Reply STOP to opt out"
- Checked by the privacy check in `tests/eval_replies.py` (§17)

## Prompt

TODO(P3): write the system prompt.
