from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_shared_mobile_api_client_uses_auth_idempotency_and_client_events() -> None:
    source = read("mobile/shared/apiClient.js")

    assert "/auth/token" in source
    assert "tokenCache" in source
    assert '"Authorization"' in source or "Authorization" in source
    assert "client_event" in source
    assert '"Idempotency-Key"' in source
    assert '"/passenger/request-ride"' in source
    assert '"/passenger/cancel"' in source
    assert '"/driver/status"' in source
    assert "authenticateUser" in source
    assert "registerRider" in source
    assert "updateLocalProfile" in source
    assert "getDriverEarnings" in source
    assert "getRideReplay" in source
    assert "getRideEvidence" in source
    assert '"/system/health"' in source
    assert '"/system/drivers"' in source
    assert '"/system/trust-metrics"' in source
    assert '"/system/pilot-metrics"' in source
    assert "/ride/${rideId}/accept" in source
    assert "/ride/${rideId}/arrive" in source
    assert "/ride/${rideId}/start" in source
    assert "/ride/${rideId}/complete" in source
    assert "/ride/${rideId}/receipt" in source


def test_rider_mobile_surface_exposes_real_execution_controls() -> None:
    source = read("mobile/passenger_app/App.js")

    assert "authenticateUser({" in source
    assert "registerRider({" in source
    assert "updateLocalProfile({" in source
    assert "requestRide({" in source
    assert "getRideStatus({" in source
    assert "cancelRide({" in source
    assert "getRideReceipt({" in source
    assert "getRideReplay({" in source
    assert "getRideEvidence({" in source
    for label in (
        "Login",
        "Register",
        "Home",
        "Request Ride",
        "Ride Tracking",
        "Ride History",
        "Receipt",
        "Replay Viewer",
        "Evidence Viewer",
        "Profile",
        "Settings",
        "Track rides",
        "View receipts",
        "View replay/evidence",
        "Manage profile",
    ):
        assert label in source
    assert "Real execution surface over rider trust endpoints." in source


def test_driver_mobile_surface_exposes_real_execution_controls() -> None:
    source = read("mobile/driver_app/App.js")

    assert "authenticateUser({" in source
    assert "updateLocalProfile({" in source
    assert "setDriverStatus({" in source
    assert "getDriverAssignedRides({" in source
    assert "getDriverEarnings({" in source
    assert "getRideReceipt({" in source
    assert "getRideReplay({" in source
    assert "acceptRide({" in source
    assert "arriveRide({" in source
    assert "startTrip({" in source
    assert "completeTrip({" in source
    for label in (
      "Login",
      "Available Rides",
      "Assigned Ride",
      "Trip Lifecycle",
      "Earnings",
      "Replay",
      "Receipt",
      "Profile",
      "Go online",
      "Go offline",
      "View earnings",
      "View receipts",
      "View replay",
      "Manage profile",
      "Accept",
      "Arrive",
      "Start",
      "Complete",
    ):
        assert label in source
    assert "Real execution surface over driver trust endpoints." in source


def test_operator_mobile_surface_exposes_real_execution_controls() -> None:
    source = read("mobile/operator_app/App.js")

    assert "getSystemHealth({" in source
    assert "getActiveRides({" in source
    assert "getDriversSnapshot({" in source
    assert "getReplayHealth({" in source
    assert "getEvidenceHealth({" in source
    assert "getTrustMetrics({" in source
    assert "getPilotMetrics({" in source
    assert "setDriverStatus({" in source
    for label in (
        "Login",
        "Dispatch",
        "Active Rides",
        "Drivers",
        "Replay Health",
        "Evidence",
        "Operations",
    ):
        assert label in source
