from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum


class AfriConnectTLStatus(str, Enum):
    PLANNED = "PLANNED"


class ShipmentStatus(str, Enum):
    REQUESTED = "REQUESTED"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"


@dataclass(frozen=True)
class Shipment:
    id: str
    sender_id: str
    receiver_id: str
    origin: str
    destination: str
    status: ShipmentStatus = ShipmentStatus.REQUESTED
    courier_id: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.id, "id")
        _require_text(self.sender_id, "sender_id")
        _require_text(self.receiver_id, "receiver_id")
        _require_text(self.origin, "origin")
        _require_text(self.destination, "destination")
        if not isinstance(self.status, ShipmentStatus):
            raise TypeError("status must be ShipmentStatus")
        if self.courier_id is not None:
            _require_text(self.courier_id, "courier_id")

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


def _require_text(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
