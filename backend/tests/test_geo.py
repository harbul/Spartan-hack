"""Unit tests for point-in-polygon: points inside, outside and on the edge.

Implements: PLAN.md §17 (test_geo.py).
Owner: P2 (Backend and infra).
"""

import pytest

from app import geo  # noqa: F401  (import check until the tests are written)


@pytest.mark.skip(reason="TODO(P2, §17)")
@pytest.mark.parametrize("case", ["inside", "outside", "edge"])
def test_point_in_polygon(case):
    ...
