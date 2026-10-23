"""Smoke test for the skeleton API: GET /health.

Implements: PLAN.md §13 H0-H1 (walking skeleton).
Owner: P2 (Backend and infra).
"""

from fastapi.testclient import TestClient

from app.main import app


def test_health():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}
