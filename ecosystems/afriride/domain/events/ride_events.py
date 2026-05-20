import uuid
from copy import deepcopy
from datetime import datetime, UTC
from typing import Any, Dict, Optional


# ======================================================
# CORE EVENT CLASS
# ======================================================

class Event:
    """
    Immutable domain event.

    Guarantees:
    - Unique identity (event_id)
    - Stable event contract
    - UTC timestamp
    - Deep-copied payload (immutability safety)
    - Replay-safe structure
    """

    def __init__(
        self,
        type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
    ):
        # --------------------------------------------------
        # CORE METADATA
        # --------------------------------------------------
        self.event_id = event_id or str(uuid.uuid4())
        self.type = type

        # Defensive copy → protects replay & mutation bugs
        self.payload = deepcopy(payload)

        # --------------------------------------------------
        # UTC TIMESTAMP (Python 3.13 safe)
        # --------------------------------------------------
        self.timestamp = timestamp or datetime.now(UTC).isoformat()

    # --------------------------------------------------
    # REPRESENTATION
    # --------------------------------------------------
    def __repr__(self):
        return (
            f"<Event "
            f"type={self.type} "
            f"id={self.event_id} "
            f"ts={self.timestamp}>"
        )

    # --------------------------------------------------
    # EQUALITY (STRICT)
    # --------------------------------------------------
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Event):
            return False

        return (
            self.event_id == other.event_id
            and self.type == other.type
            and self.payload == other.payload
            and self.timestamp == other.timestamp
        )

    # --------------------------------------------------
    # HASH (ENABLE SET/DICT USAGE)
    # --------------------------------------------------
    def __hash__(self):
        return hash((self.event_id, self.type, self.timestamp))

    # --------------------------------------------------
    # SERIALIZATION
    # --------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type,
            "payload": deepcopy(self.payload),
            "timestamp": self.timestamp,
        }

    # --------------------------------------------------
    # DESERIALIZATION
    # --------------------------------------------------
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            type=data["type"],
            payload=data["payload"],
            event_id=data.get("event_id"),
            timestamp=data.get("timestamp"),
        )


# ======================================================
# RIDE LIFECYCLE EVENTS
# ======================================================

def RideRequested(
    ride_id: Optional[str] = None,
    rider_id: Optional[str] = None,
    pickup: Optional[Dict[str, Any]] = None,
    dropoff: Optional[Dict[str, Any]] = None,
):
    """
    Backward-compatible constructor.

    - If ride_id missing → auto-generated
    - Enforces required business fields
    """

    if rider_id is None:
        raise Exception("rider_id is required")

    if pickup is None or dropoff is None:
        raise Exception("pickup and dropoff are required")

    ride_id = ride_id or str(uuid.uuid4())

    return Event(
        "RideRequested",
        {
            "ride_id": ride_id,
            "rider_id": rider_id,
            "pickup": pickup,
            "dropoff": dropoff,
        }
    )


def DriverAssigned(ride_id: str, driver_id: str):
    return Event(
        "DriverAssigned",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
        }
    )


def TripStarted(ride_id: str):
    return Event(
        "TripStarted",
        {"ride_id": ride_id},
    )


def TripCompleted(ride_id: str):
    return Event(
        "TripCompleted",
        {"ride_id": ride_id},
    )


def TripCancelled(ride_id: str, reason: Optional[str] = None):
    payload = {"ride_id": ride_id}

    if reason:
        payload["reason"] = reason

    return Event(
        "TripCancelled",
        payload,
    )


# ======================================================
# DISPATCH EVENTS
# ======================================================

def DriverOffered(ride_id: str, driver_id: str, attempt: int):
    return Event(
        "DriverOffered",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "attempt": attempt,
        }
    )


def OfferExpired(ride_id: str, driver_id: str, attempt: int):
    return Event(
        "OfferExpired",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "attempt": attempt,
        }
    )


def DriverAccepted(ride_id: str, driver_id: str, attempt: int):
    return Event(
        "DriverAccepted",
        {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "attempt": attempt,
        }
    )


# ======================================================
# DRIVER PRESENCE EVENTS (REAL-TIME / SIDE SYSTEM)
# ======================================================

def DriverOnline(driver_id: str, lat: float, lng: float):
    return Event(
        "DriverOnline",
        {
            "driver_id": driver_id,
            "lat": lat,
            "lng": lng,
        }
    )


def DriverLocationUpdated(driver_id: str, lat: float, lng: float):
    return Event(
        "DriverLocationUpdated",
        {
            "driver_id": driver_id,
            "lat": lat,
            "lng": lng,
        }
    )


def DriverOffline(driver_id: str):
    return Event(
        "DriverOffline",
        {
            "driver_id": driver_id,
        }
    )


# ======================================================
# UTILITY HELPERS
# ======================================================

def event_type(event: Event) -> str:
    return event.type


def event_stream_key(event: Event) -> Any:
    """
    Determine stream partition key.

    Priority:
    - ride_id
    - driver_id
    - fallback → global
    """

    payload = event.payload

    if "ride_id" in payload:
        return payload["ride_id"]

    if "driver_id" in payload:
        return payload["driver_id"]

    return "global"
