"""Pure geometry helpers: point-in-polygon (ray casting) and nearest resource.

No AWS calls here, so it is easy to unit test (tests/test_geo.py).

Implements: PLAN.md §8 (POST /outages affected residents), §4 Job 5 (find_nearest_resource).
Owner: P2 (Backend and infra).
"""

import math
from typing import Any

from app.schemas import Resource, ResourceType

EARTH_RADIUS_KM = 6371.0


def point_in_polygon(lat: float, lng: float, polygon: dict[str, Any]) -> bool:
    """Ray casting over a GeoJSON Polygon's outer ring (coordinates are [lng, lat]).

    Points exactly on an edge may land either way; demo homes are never on the edge.
    """
    ring = polygon["coordinates"][0]
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > lat) != (y2 > lat) and lng < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle (haversine) distance."""
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * math.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def nearest_resource(
    lat: float, lng: float, type: ResourceType, resources: list[Resource]
) -> Resource | None:
    """Closest resource of the given type by straight-line distance."""
    candidates = [r for r in resources if r.type == type]
    return min(candidates, key=lambda r: distance_km(lat, lng, r.lat, r.lng), default=None)
