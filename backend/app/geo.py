"""Pure geometry helpers: point-in-polygon (ray casting) and nearest resource.

No AWS calls here, so it is easy to unit test (tests/test_geo.py).

Implements: PLAN.md §8 (POST /outages affected residents), §4 Job 5 (find_nearest_resource).
Owner: P2 (Backend and infra).
"""

from typing import Any

from app.schemas import Resource, ResourceType


def point_in_polygon(lat: float, lng: float, polygon: dict[str, Any]) -> bool:
    """Ray casting over a GeoJSON Polygon's outer ring (coordinates are [lng, lat])."""
    ...


def nearest_resource(
    lat: float, lng: float, type: ResourceType, resources: list[Resource]
) -> Resource | None:
    """Closest resource of the given type by straight-line distance."""
    ...
