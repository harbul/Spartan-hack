"""Shared test fixtures: an in-memory stand-in for the DynamoDB tables (no AWS calls).

FakeTable supports what store.py uses: put_item, get_item, query on the partition
key, scan, batch_writer and key_schema.
Owner: P2 (Backend and infra).
"""

import pytest

from app import store

KEYS = {
    "RESIDENTS_TABLE": ["resident_id"],
    "OUTAGES_TABLE": ["outage_id"],
    "CASES_TABLE": ["outage_id", "resident_id"],
    "MESSAGES_TABLE": ["resident_id", "ts"],
    "PLANS_TABLE": ["plan_id"],
    "TRACES_TABLE": ["trace_id"],
    "EVENTS_TABLE": ["outage_id", "sk"],
    "CONFIG_TABLE": ["key"],
}


class FakeTable:
    def __init__(self, keys):
        self.keys = keys
        self.key_schema = [{"AttributeName": k} for k in keys]
        self.items = {}

    def _id(self, item):
        return tuple(item[k] for k in self.keys)

    def put_item(self, Item):
        self.items[self._id(Item)] = Item

    def delete_item(self, Key):
        self.items.pop(self._id(Key), None)

    def get_item(self, Key):
        item = self.items.get(self._id(Key))
        return {"Item": item} if item else {}

    def scan(self, **kwargs):
        return {"Items": list(self.items.values())}

    def query(self, KeyConditionExpression, ScanIndexForward=True, **kwargs):
        key, value = KeyConditionExpression.get_expression()["values"]
        rows = [i for i in self.items.values() if i[key.name] == value]
        sort_key = self.keys[1] if len(self.keys) > 1 else self.keys[0]
        return {"Items": sorted(rows, key=lambda i: i[sort_key], reverse=not ScanIndexForward)}

    def batch_writer(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def tables(monkeypatch):
    """Fake tables keyed by env var name, wired into store._table."""
    fakes = {name: FakeTable(keys) for name, keys in KEYS.items()}
    monkeypatch.setattr(store, "_table", lambda env_name: fakes[env_name])
    return fakes
