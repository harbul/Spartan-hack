"""Amazon Location Service routes client (boto3 `geo-routes`).

OptimizeWaypoints picks the stop order; CalculateRoutes returns duration,
distance and a GeoJSON geometry for the map. Fallback if either fails:
straight-line legs (§16).

Implements: PLAN.md §4 Job 5 (optimize_run), §6 (Amazon Location).
Owner: P2 (Backend and infra).
"""

from typing import Any


def optimize_waypoints(start: dict[str, float], stops: list[dict[str, float]]) -> list[int]:
    """Return the indexes of `stops` in the fastest visit order."""
    ...


def calculate_route(waypoints: list[dict[str, float]]) -> dict[str, Any]:
    """Return {duration_min, distance_km, geometry} for the ordered waypoints."""
    ...
