"""DynamoDB access for every table in the data model, plus the demo reseed.

Table names come from env vars (RESIDENTS_TABLE, CASES_TABLE, ...; see
.env.example). Converts floats to Decimal on the way in and back on the way out.
Only this file talks to DynamoDB.

Implements: PLAN.md §7 (data model), §8 (POST /demo/reset).
Owner: P2 (Backend and infra).
"""

from app.schemas import Case, Event, Message, Outage, Plan, Resident, Trace


def reset_demo() -> None:
    """Reseed residents and config from data/, clear cases, messages, plans, traces, events."""
    ...


def list_residents() -> list[Resident]:
    ...


def put_outage(outage: Outage) -> None:
    ...


def get_outage(outage_id: str) -> Outage | None:
    ...


def put_case(case: Case) -> None:
    ...


def list_cases(outage_id: str) -> list[Case]:
    ...


def add_message(message: Message) -> None:
    ...


def list_messages(resident_id: str) -> list[Message]:
    ...


def put_plan(plan: Plan) -> None:
    ...


def get_plan(plan_id: str) -> Plan | None:
    ...


def put_trace(trace: Trace) -> None:
    ...


def list_traces(limit: int = 50) -> list[Trace]:
    ...


def add_event(event: Event) -> None:
    ...


def list_events(outage_id: str) -> list[Event]:
    ...


def get_config(key: str):
    """Read `clock_offset_min`, `volunteers` or `resources` from the config table."""
    ...


def set_config(key: str, value) -> None:
    ...
