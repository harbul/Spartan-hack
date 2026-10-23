"""Unit tests for the deterministic triage score: score and band for each hero resident.

Implements: PLAN.md §17 (test_triage.py), §5, §3 (hero residents).
Owner: P2 (Backend and infra).
"""

import pytest

from app import triage  # noqa: F401  (import check until the tests are written)

HERO_RESIDENTS = ["Trần Văn Minh", "Rosa Delgado", "Harold Kim", "Denise Okafor", "Lupe Ramírez"]


@pytest.mark.skip(reason="TODO(P2, §17): expected score and band per hero resident")
@pytest.mark.parametrize("name", HERO_RESIDENTS)
def test_hero_resident_score_and_band(name):
    ...
