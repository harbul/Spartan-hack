"""DynamoDB access for every table in the data model, plus the demo reseed.

Table names come from env vars (RESIDENTS_TABLE, CASES_TABLE, ...; see
.env.example). Converts floats to Decimal on the way in and back on the way out.
Only this file talks to DynamoDB.

Seed data: data/ is read from SEED_DIR, else backend/data (a symlink to ../data
that `sam build` copies into the Lambda), else the repo-root data/.

Implements: PLAN.md §7 (data model), §8 (POST /demo/reset).
Owner: P2 (Backend and infra).
"""

import json
import os
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel

from app.schemas import Case, Event, Message, Outage, Plan, Resident, Resource, Trace, Volunteer

_HERE = Path(__file__).resolve().parent
SEED_DIRS = [_HERE.parent / "data", _HERE.parents[1] / "data"]

# Tables cleared by /demo/reset. `residents` is cleared and reseeded too.
_RUN_TABLES = [
    "CASES_TABLE",
    "MESSAGES_TABLE",
    "PLANS_TABLE",
    "TRACES_TABLE",
    "EVENTS_TABLE",
    "OUTAGES_TABLE",
]


class StoreNotConfigured(RuntimeError):
    """A table env var is missing. Set it in .env (local) or get it from the SAM stack (Lambda)."""


# --- plumbing -----------------------------------------------------------------


@lru_cache(maxsize=1)
def _dynamodb():
    return boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION") or None)


@lru_cache(maxsize=None)
def _table(env_name: str):
    name = os.environ.get(env_name, "").strip()
    if not name:
        raise StoreNotConfigured(f"{env_name} is not set (see .env.example)")
    return _dynamodb().Table(name)


def _to_item(data: BaseModel | dict[str, Any]) -> dict[str, Any]:
    """Model or dict -> DynamoDB item (floats become Decimal)."""
    text = data.model_dump_json() if isinstance(data, BaseModel) else json.dumps(data)
    return json.loads(text, parse_float=Decimal)


def _plain(value: Any) -> Any:
    """DynamoDB item -> plain Python (Decimal becomes int or float)."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_plain(v) for v in value]
    return value


def _scan_all(table, **kwargs) -> list[dict[str, Any]]:
    items, start = [], None
    while True:
        page = table.scan(**kwargs, **({"ExclusiveStartKey": start} if start else {}))
        items += page.get("Items", [])
        start = page.get("LastEvaluatedKey")
        if not start:
            return items


def _query_all(table, pk: str, value: str, ascending: bool = True) -> list[dict[str, Any]]:
    items, start = [], None
    while True:
        page = table.query(
            KeyConditionExpression=Key(pk).eq(value),
            ScanIndexForward=ascending,
            **({"ExclusiveStartKey": start} if start else {}),
        )
        items += page.get("Items", [])
        start = page.get("LastEvaluatedKey")
        if not start:
            return items


def _clear(table) -> None:
    keys = [k["AttributeName"] for k in table.key_schema]
    with table.batch_writer() as batch:
        for item in _scan_all(table):
            batch.delete_item(Key={k: item[k] for k in keys})


# --- seed data (data/*.json) --------------------------------------------------


def seed_dir() -> Path:
    candidates = [Path(os.environ["SEED_DIR"])] if os.environ.get("SEED_DIR") else SEED_DIRS
    for path in candidates:
        if (path / "residents.json").is_file():
            return path
    raise FileNotFoundError(f"No seed data in {', '.join(map(str, candidates))}")


def load_seed(name: str) -> list[dict[str, Any]]:
    """The list in data/<name>.json (e.g. "residents"); the `_meta` block is skipped."""
    return json.loads((seed_dir() / f"{name}.json").read_text(encoding="utf-8"))[name]


def reset_demo() -> None:
    """Reseed residents and config from data/, clear cases, messages, plans, traces, events."""
    for env_name in _RUN_TABLES:
        _clear(_table(env_name))

    residents = _table("RESIDENTS_TABLE")
    _clear(residents)
    with residents.batch_writer() as batch:
        for row in load_seed("residents"):
            batch.put_item(Item=_to_item(Resident.model_validate(row)))

    set_config("clock_offset_min", 0)
    set_config("volunteers", [Volunteer.model_validate(v).model_dump() for v in load_seed("volunteers")])
    set_config("resources", [Resource.model_validate(r).model_dump() for r in load_seed("resources")])


# --- residents ------------------------------------------------------------------


def list_residents() -> list[Resident]:
    return [Resident.model_validate(_plain(i)) for i in _scan_all(_table("RESIDENTS_TABLE"))]


# --- outages and cases ----------------------------------------------------------


def put_outage(outage: Outage) -> None:
    _table("OUTAGES_TABLE").put_item(Item=_to_item(outage))


def get_outage(outage_id: str) -> Outage | None:
    item = _table("OUTAGES_TABLE").get_item(Key={"outage_id": outage_id}).get("Item")
    return Outage.model_validate(_plain(item)) if item else None


def put_case(case: Case) -> None:
    _table("CASES_TABLE").put_item(Item=_to_item(case))


def put_cases(cases: list[Case]) -> None:
    with _table("CASES_TABLE").batch_writer() as batch:
        for case in cases:
            batch.put_item(Item=_to_item(case))


def list_cases(outage_id: str) -> list[Case]:
    items = _query_all(_table("CASES_TABLE"), "outage_id", outage_id)
    return [Case.model_validate(_plain(i)) for i in items]


# --- messages, plans, traces, events ----------------------------------------------


def add_message(message: Message) -> None:
    _table("MESSAGES_TABLE").put_item(Item=_to_item(message))


def list_messages(resident_id: str) -> list[Message]:
    items = _query_all(_table("MESSAGES_TABLE"), "resident_id", resident_id)
    return [Message.model_validate(_plain(i)) for i in items]


def put_plan(plan: Plan) -> None:
    _table("PLANS_TABLE").put_item(Item=_to_item(plan))


def get_plan(plan_id: str) -> Plan | None:
    item = _table("PLANS_TABLE").get_item(Key={"plan_id": plan_id}).get("Item")
    return Plan.model_validate(_plain(item)) if item else None


def put_trace(trace: Trace) -> None:
    _table("TRACES_TABLE").put_item(Item=_to_item(trace))


def list_traces(limit: int = 50) -> list[Trace]:
    """Newest first. Scan + sort is fine at demo scale (a few hundred rows)."""
    items = sorted(_scan_all(_table("TRACES_TABLE")), key=lambda i: i["ts"], reverse=True)
    return [Trace.model_validate(_plain(i)) for i in items[:limit]]


def add_event(event: Event) -> None:
    _table("EVENTS_TABLE").put_item(Item=_to_item(event))


def list_events(outage_id: str) -> list[Event]:
    items = _query_all(_table("EVENTS_TABLE"), "outage_id", outage_id)
    return [Event.model_validate(_plain(i)) for i in items]


# --- config -----------------------------------------------------------------------


def get_config(key: str):
    """Read `clock_offset_min`, `volunteers` or `resources` from the config table."""
    item = _table("CONFIG_TABLE").get_item(Key={"key": key}).get("Item")
    return _plain(item["value"]) if item else None


def set_config(key: str, value) -> None:
    _table("CONFIG_TABLE").put_item(Item=_to_item({"key": key, "value": value}))
