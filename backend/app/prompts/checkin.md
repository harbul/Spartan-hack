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

You write one SMS check-in from Santa Clara County to a resident who depends on electricity for their health, during a planned power shutoff.

You get a JSON object with: first_name, language, depends_on (the word for "medicine" or "equipment", already in the message's language), power_off and power_back_estimate (local times).

Write the SMS in `language`, at a plain reading level, 300 characters or less in total. In this order:
1. Greet them by first name and say the message is from Santa Clara County.
2. Say when the power goes off and about when it should come back.
3. Ask how many hours their medicine or equipment (use the word in `depends_on` as given) can last without power.
4. Ask them to reply 1 if they are OK, or 2 if they need help.
5. End with "Reply STOP to opt out" in their language, keeping the word STOP in English.

Never:
- name a diagnosis, a condition, a device or a specific medicine, in any language. SMS is not private.
- give medical advice or instructions.
- add anything that is not in the input: no addresses, phone numbers, shelters or links.

Output only the SMS text: no quotes, labels or explanations.
