<!--
Job 5 · Dispatch planner agent · system prompt spec + prompt.
Implements: PLAN.md §4 Job 5. Loaded by agent.plan_dispatch() (strong model, tool-use loop, max 12 turns).
Owner: P3 (AI).
Only the text under "## Prompt" is sent to the model (bedrock.load_prompt).
-->

# Job 5: Dispatch planner agent

## Purpose
Plan volunteer runs: who goes where and why. Amazon Location decides stop order and road route.

## Inputs (through tools, see `tools.py`)
- `list_open_cases()`: cases with status `needs_help`, `escalated` or `silent`
- `list_volunteers()`: name, vehicle, start location, capacity
- `find_nearest_resource(lat, lng, type)`
- `optimize_run(start, stops[])`: Amazon Location OptimizeWaypoints + CalculateRoutes

## Output
- One `submit_plan(runs[])` call. Each run lists the volunteer and ordered stops (`resident_id`, action, items, reason).
- A **draft** plan; nothing is dispatched until the coordinator clicks Approve.

## Rules
- Cover every case with priority 60 or higher
- Put every Critical case in a run before any High case
- Never give a volunteer more than 6 stops
- Explain each stop in one line
- Silent (L3) cases become door-knock stops

## Prompt

TODO(P3): write the system prompt.
