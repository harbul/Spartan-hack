"""Unit tests for point-in-polygon (inside, outside, near the edge) and nearest resource.

Implements: PLAN.md §17 (test_geo.py).
Owner: P2 (Backend and infra).
"""

import pytest

from app import geo
from app.schemas import Resource

SQUARE = {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]]}
# Concave "C" shape: the notch (x 3..10, y 3..7) is outside.
C_SHAPE = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [10, 0], [10, 3], [3, 3], [3, 7], [10, 7], [10, 10], [0, 10], [0, 0]]],
}


@pytest.mark.parametrize(
    "lat, lng, expected",
    [
        (5, 5, True),  # inside
        (0.001, 9.999, True),  # just inside a corner
        (5, 10.001, False),  # just outside the right edge
        (-1, 5, False),  # below
        (5, -0.001, False),  # just outside the left edge
    ],
)
def test_point_in_square(lat, lng, expected):
    assert geo.point_in_polygon(lat, lng, SQUARE) is expected


def test_concave_notch_is_outside():
    assert geo.point_in_polygon(5, 6, C_SHAPE) is False
    assert geo.point_in_polygon(5, 1, C_SHAPE) is True
    assert geo.point_in_polygon(8, 8, C_SHAPE) is True


def test_unclosed_ring_still_works():
    open_ring = {"type": "Polygon", "coordinates": [[[0, 0], [10, 0], [10, 10], [0, 10]]]}
    assert geo.point_in_polygon(5, 5, open_ring) is True
    assert geo.point_in_polygon(5, 11, open_ring) is False


def _resource(rid, type_, lat, lng):
    return Resource(resource_id=rid, name=rid, type=type_, address="", lat=lat, lng=lng)


def test_nearest_resource_by_type():
    resources = [
        _resource("far-crc", "resource_center", 37.40, -121.70),
        _resource("near-crc", "resource_center", 37.37, -121.80),
        _resource("pharm", "pharmacy", 37.3701, -121.8001),
    ]
    assert geo.nearest_resource(37.37, -121.80, "resource_center", resources).resource_id == "near-crc"
    assert geo.nearest_resource(37.37, -121.80, "pharmacy", resources).resource_id == "pharm"
    assert geo.nearest_resource(37.37, -121.80, "pharmacy", resources[:2]) is None


def test_distance_km():
    # ~1 degree of latitude is ~111 km
    assert geo.distance_km(37, -121, 38, -121) == pytest.approx(111.2, abs=0.5)
