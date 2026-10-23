"""Job 5: the dispatch planner agent (Converse tool-use loop, strong model).

The agent decides who goes where and why; Amazon Location decides stop
order and road route (via tools.optimize_run). Output is a draft plan only.

Implements: PLAN.md §4 Job 5, §16 (greedy fallback planner).
Owner: P3 (AI).
"""

from app.schemas import Plan

MAX_TURNS = 12


def plan_dispatch(outage_id: str) -> Plan:
    """Run the tool-use loop with prompts/planner.md and tools.AGENT_TOOLS until submit_plan."""
    ...


def greedy_plan(outage_id: str) -> Plan:
    """Fallback if the agent loops or fails: priority first, then nearest neighbor."""
    ...
