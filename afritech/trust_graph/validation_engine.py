from __future__ import annotations

from typing import Any


VALID_ACTION_TYPES = {
    "DriverAvailabilityChanged",
    "DriverStatusReported",
    "RideAccepted",
    "RideRejected",
    "DriverArrived",
    "TripStarted",
    "TripCompleted",
    "ManualTrustEvent",
    "PilotEvidenceCaptured",
}


def validate_proposal(proposal: dict[str, Any]) -> dict[str, Any]:
    change = proposal.get("change") or {}
    event_type = proposal.get("type", "")
    details: list[dict[str, Any]] = []

    details.append(
        {
            "check": "payload_present",
            "passed": bool(change),
            "message": "Proposal change payload must not be empty",
        }
    )
    details.append(
        {
            "check": "valid_action_type",
            "passed": event_type in VALID_ACTION_TYPES,
            "message": "Proposal type must be registered in the trust contract",
        }
    )

    if event_type.startswith("Ride") or event_type.startswith("Trip"):
        details.append(
            {
                "check": "has_ride_id",
                "passed": bool(change.get("ride_id")),
                "message": "Ride events must carry ride_id",
            }
        )

    if event_type in {"RideAccepted", "DriverArrived", "TripStarted", "TripCompleted"}:
        details.append(
            {
                "check": "has_driver_id",
                "passed": bool(change.get("driver_id")),
                "message": "Driver execution events must carry driver_id",
            }
        )

    passed = all(item["passed"] for item in details)
    return {
        "passed": passed,
        "details": details,
        "risk": "LOW" if passed else "HIGH",
    }
