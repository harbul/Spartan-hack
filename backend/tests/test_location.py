"""Tests for the Amazon Location routes client, with a stubbed geo-routes client (no AWS calls).

Implements: PLAN.md §4 Job 5 (optimize_run), §16 (straight-line fallback).
Owner: P2 (Backend and infra).
"""

import boto3
import pytest
from botocore.stub import ANY, Stubber

from app import location

START = {"lat": 37.35, "lng": -121.84}
STOPS = [{"lat": 37.39, "lng": -121.80}, {"lat": 37.36, "lng": -121.83}, {"lat": 37.37, "lng": -121.81}]


@pytest.fixture
def stub(monkeypatch):
    client = boto3.client("geo-routes", region_name="us-west-2", aws_access_key_id="t", aws_secret_access_key="t")
    monkeypatch.setattr(location, "_client", lambda: client)
    with Stubber(client) as stubber:
        yield stubber


def test_optimize_maps_ids_back_to_stop_indexes(stub):
    stub.add_response(
        "optimize_waypoints",
        {
            "OptimizedWaypoints": [
                {"Id": "origin", "Position": [-121.84, 37.35], "DepartureTime": "2026-10-24T01:00:00Z"},
                {"Id": "s1", "Position": [-121.83, 37.36], "ArrivalTime": "2026-10-24T01:05:00Z", "DepartureTime": "2026-10-24T01:05:00Z"},
                {"Id": "s2", "Position": [-121.81, 37.37], "ArrivalTime": "2026-10-24T01:10:00Z", "DepartureTime": "2026-10-24T01:10:00Z"},
                {"Id": "s0", "Position": [-121.80, 37.39], "ArrivalTime": "2026-10-24T01:15:00Z", "DepartureTime": "2026-10-24T01:15:00Z"},
            ],
            "Connections": [], "Distance": 9000, "Duration": 900, "ImpedingWaypoints": [], "PricingBucket": "x",
            "TimeBreakdown": {"RestDuration": 0, "ServiceDuration": 0, "TravelDuration": 900, "WaitDuration": 0},
        },
        {"Origin": [-121.84, 37.35], "Waypoints": ANY, "TravelMode": "Car"},
    )
    assert location.optimize_waypoints(START, STOPS) == ([1, 2, 0], False)


def test_route_joins_legs_and_converts_units(stub):
    leg = lambda coords: {"Geometry": {"LineString": coords}, "TravelMode": "Car", "Type": "Vehicle"}  # noqa: E731
    stub.add_response(
        "calculate_routes",
        {
            "Routes": [{
                "Legs": [leg([[-121.84, 37.35], [-121.83, 37.36]]), leg([[-121.83, 37.36], [-121.80, 37.39]])],
                "MajorRoadLabels": [],
                "Summary": {"Distance": 6400, "Duration": 780},
            }],
            "LegGeometryFormat": "Simple", "Notices": [], "PricingBucket": "x",
        },
        {"Origin": [-121.84, 37.35], "Destination": [-121.80, 37.39], "Waypoints": [{"Position": [-121.83, 37.36]}],
         "TravelMode": "Car", "LegGeometryFormat": "Simple"},
    )
    route = location.calculate_route([START, STOPS[1], STOPS[0]])
    assert route["geometry"]["coordinates"] == [[-121.84, 37.35], [-121.83, 37.36], [-121.80, 37.39]]
    assert (route["distance_km"], route["duration_min"], route["fallback"]) == (6.4, 13.0, False)


def test_fallbacks_when_location_fails(stub):
    stub.add_client_error("optimize_waypoints", "AccessDeniedException")
    stub.add_client_error("calculate_routes", "ValidationException")
    order, fallback = location.optimize_waypoints(START, STOPS)
    assert fallback and order == [1, 2, 0]  # nearest neighbour from START
    route = location.calculate_route([START] + [STOPS[i] for i in order])
    assert route["fallback"] and len(route["geometry"]["coordinates"]) == 4
    assert route["duration_min"] == pytest.approx(route["distance_km"] / 30 * 60, abs=0.2)


def test_single_stop_needs_no_call():
    assert location.optimize_waypoints(START, STOPS[:1]) == ([0], False)
    assert location.calculate_route([START])["distance_km"] == 0
