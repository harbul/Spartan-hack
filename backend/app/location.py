"""Amazon Location Service routes client (boto3 `geo-routes`).

OptimizeWaypoints picks the stop order; CalculateRoutes returns duration,
distance and a GeoJSON geometry for the map. Fallback if either fails:
straight-line legs (§16).

Implements: PLAN.md §4 Job 5 (optimize_run), §6 (Amazon Location).
Owner: P2 (Backend and infra).
"""

import logging
import os
import threading
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app import geo

log = logging.getLogger(__name__)
FALLBACK_KMH = 30  # straight-line legs at town driving speed (§16)
_local = threading.local()


def _client():
    """geo-routes client, one per thread (the agent and the plan builder can run in parallel)."""
    if not hasattr(_local, "client"):
        _local.client = boto3.session.Session().client(
            "geo-routes", region_name=os.environ.get("AWS_REGION") or None
        )
    return _local.client


def _position(point: dict[str, float]) -> list[float]:
    return [point["lng"], point["lat"]]


def _nearest_neighbour(start: dict[str, float], stops: list[dict[str, float]]) -> list[int]:
    order, here, left = [], start, list(range(len(stops)))
    while left:
        nxt = min(left, key=lambda i: geo.distance_km(here["lat"], here["lng"], stops[i]["lat"], stops[i]["lng"]))
        order.append(nxt)
        left.remove(nxt)
        here = stops[nxt]
    return order


def optimize_waypoints(start: dict[str, float], stops: list[dict[str, float]]) -> tuple[list[int], bool]:
    """Return the indexes of `stops` in the fastest visit order, and whether it is the fallback.

    Fallback (§16): nearest neighbour by straight-line distance.
    """
    if len(stops) < 2:
        return list(range(len(stops))), False
    try:
        response = _client().optimize_waypoints(
            Origin=_position(start),
            Waypoints=[{"Id": f"s{i}", "Position": _position(p)} for i, p in enumerate(stops)],
            TravelMode="Car",
        )
        order = [int(w["Id"][1:]) for w in response["OptimizedWaypoints"] if w.get("Id", "").startswith("s")]
        if sorted(order) == list(range(len(stops))):
            return order, False
        log.warning("OptimizeWaypoints returned an incomplete order; using nearest neighbour")
    except (ClientError, BotoCoreError) as err:
        log.warning("OptimizeWaypoints failed, using nearest neighbour: %s", err)
    return _nearest_neighbour(start, stops), True


def calculate_route(waypoints: list[dict[str, float]]) -> dict[str, Any]:
    """Return {duration_min, distance_km, geometry, fallback} for the ordered waypoints.

    Driving time only (no time at each stop). Fallback (§16): straight-line legs at 30 km/h.
    """
    if len(waypoints) < 2:
        return {"duration_min": 0.0, "distance_km": 0.0, "geometry": None, "fallback": False}
    try:
        response = _client().calculate_routes(
            Origin=_position(waypoints[0]),
            Destination=_position(waypoints[-1]),
            Waypoints=[{"Position": _position(p)} for p in waypoints[1:-1]],
            TravelMode="Car",
            LegGeometryFormat="Simple",
        )
        route = response["Routes"][0]
        coordinates: list[list[float]] = []
        for leg in route["Legs"]:
            line = leg.get("Geometry", {}).get("LineString", [])
            coordinates += line[1:] if coordinates and line and line[0] == coordinates[-1] else line
        return {
            "duration_min": round(route["Summary"]["Duration"] / 60, 1),
            "distance_km": round(route["Summary"]["Distance"] / 1000, 2),
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "fallback": False,
        }
    except (ClientError, BotoCoreError, KeyError, IndexError) as err:
        log.warning("CalculateRoutes failed, using straight lines: %s", err)
    km = sum(
        geo.distance_km(a["lat"], a["lng"], b["lat"], b["lng"]) for a, b in zip(waypoints, waypoints[1:])
    )
    return {
        "duration_min": round(km / FALLBACK_KMH * 60, 1),
        "distance_km": round(km, 2),
        "geometry": {"type": "LineString", "coordinates": [_position(p) for p in waypoints]},
        "fallback": True,
    }
