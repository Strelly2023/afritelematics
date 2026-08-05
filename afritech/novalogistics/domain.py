"""Immutable, tenant-aware NovaLogistics domain foundation.

The module deliberately contains no persistence or transport concerns. Aggregate
transitions return new values and append deterministic domain events, making the
contracts safe for replay and for the durable adapters introduced in NL-002.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, TypeVar


SCHEMA_VERSION = "afritech.novalogistics.domain.v1"


class DomainError(ValueError):
    """Base error for invalid domain values and transitions."""


class InvalidTransition(DomainError):
    """Raised when an aggregate lifecycle transition is not allowed."""


def _text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(f"{field_name} is required")
    return " ".join(value.strip().split())


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise DomainError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, order=True)
class Identifier:
    value: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "value", _text(self.value, "identifier"))

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class GeoCoordinate:
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        if not -90 <= self.latitude <= 90:
            raise DomainError("latitude must be between -90 and 90")
        if not -180 <= self.longitude <= 180:
            raise DomainError("longitude must be between -180 and 180")


@dataclass(frozen=True)
class Address:
    line1: str
    locality: str
    country_code: str
    postal_code: str = ""
    line2: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "line1", _text(self.line1, "line1"))
        object.__setattr__(self, "locality", _text(self.locality, "locality"))
        code = _text(self.country_code, "country_code").upper()
        if len(code) != 2 or not code.isalpha():
            raise DomainError("country_code must be ISO 3166-1 alpha-2")
        object.__setattr__(self, "country_code", code)
        object.__setattr__(self, "postal_code", self.postal_code.strip())
        object.__setattr__(self, "line2", " ".join(self.line2.strip().split()))


@dataclass(frozen=True)
class Contact:
    name: str
    email: str = ""
    phone: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "name"))
        email = self.email.strip().lower()
        phone = self.phone.strip()
        if not email and not phone:
            raise DomainError("contact requires email or phone")
        if email and ("@" not in email or email.startswith("@") or email.endswith("@")):
            raise DomainError("email is invalid")
        object.__setattr__(self, "email", email)
        object.__setattr__(self, "phone", phone)


@dataclass(frozen=True)
class DomainEvent:
    event_type: str
    aggregate_id: Identifier
    tenant_id: Identifier
    occurred_at: datetime
    data: Mapping[str, Any] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", _text(self.event_type, "event_type"))
        object.__setattr__(self, "occurred_at", _utc(self.occurred_at))
        object.__setattr__(self, "data", MappingProxyType(dict(self.data)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "aggregate_id": str(self.aggregate_id),
            "data": dict(self.data),
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "schema_version": self.schema_version,
            "tenant_id": str(self.tenant_id),
        }


@dataclass(frozen=True)
class Entity:
    id: Identifier
    tenant_id: Identifier
    name: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _text(self.name, "name"))

    def to_dict(self) -> dict[str, Any]:
        return {"id": str(self.id), "tenant_id": str(self.tenant_id), "name": self.name}


def _entity_type(name: str) -> type[Entity]:
    return dataclass(frozen=True)(type(name, (Entity,), {"__module__": __name__}))


_ENTITY_NAMES = (
    "Tenant LegalEntity BusinessUnit Location Customer Supplier Carrier Driver Vehicle Trailer "
    "Warehouse Dock Zone BinLocation Item SKU HandlingUnit Package Pallet ShipmentLeg Route "
    "PurchaseOrder SalesOrder Rate ServiceLevel TrackingEvent ProofOfDelivery InvoiceReference "
    "PaymentReference SettlementReference"
).split()
globals().update({name: _entity_type(name) for name in _ENTITY_NAMES})


class QuoteStatus(str, Enum):
    DRAFT = "draft"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OrderStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    FULFILLED = "fulfilled"
    CANCELLED = "cancelled"


class ShipmentStatus(str, Enum):
    DRAFT = "draft"
    BOOKED = "booked"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class LoadStatus(str, Enum):
    SCHEDULED = "scheduled"
    TENDERED = "tendered"
    ACCEPTED = "accepted"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StopStatus(str, Enum):
    SCHEDULED = "scheduled"
    ARRIVED = "arrived"
    SERVICED = "serviced"
    SKIPPED = "skipped"


class PickupStatus(str, Enum):
    SCHEDULED = "scheduled"
    ARRIVED = "arrived"
    COLLECTED = "collected"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    SCHEDULED = "scheduled"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReturnStatus(str, Enum):
    REQUESTED = "requested"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    REJECTED = "rejected"


class ClaimStatus(str, Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SETTLED = "settled"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


S = TypeVar("S", bound=Enum)
L = TypeVar("L", bound="LifecycleAggregate[Any]")


@dataclass(frozen=True)
class LifecycleAggregate:
    id: Identifier
    tenant_id: Identifier
    status: Enum
    version: int = 0
    events: tuple[DomainEvent, ...] = ()

    STATUS: ClassVar[type[Enum]]
    TRANSITIONS: ClassVar[Mapping[Enum, frozenset[Enum]]]

    def __post_init__(self) -> None:
        if not isinstance(self.status, self.STATUS):
            try:
                object.__setattr__(self, "status", self.STATUS(self.status))
            except (TypeError, ValueError) as exc:
                raise DomainError(f"invalid {type(self).__name__} status") from exc
        if self.version < 0:
            raise DomainError("version cannot be negative")
        object.__setattr__(self, "events", tuple(self.events))

    def transition(self: L, target: Enum | str, *, at: datetime, reason: str = "") -> L:
        try:
            normalized = self.STATUS(target)
        except (TypeError, ValueError) as exc:
            raise InvalidTransition(f"unknown target state: {target}") from exc
        if normalized == self.status:
            return self
        if normalized not in self.TRANSITIONS.get(self.status, frozenset()):
            raise InvalidTransition(f"{self.status.value} -> {normalized.value} is not allowed")
        event = DomainEvent(
            event_type=f"{type(self).__name__}.{normalized.value}",
            aggregate_id=self.id,
            tenant_id=self.tenant_id,
            occurred_at=at,
            data={"from": self.status.value, "to": normalized.value, "reason": reason.strip()},
        )
        return replace(self, status=normalized, version=self.version + 1, events=self.events + (event,))

    def to_dict(self) -> dict[str, Any]:
        return {
            "events": [event.to_dict() for event in self.events],
            "id": str(self.id),
            "schema_version": SCHEMA_VERSION,
            "status": self.status.value,
            "tenant_id": str(self.tenant_id),
            "type": type(self).__name__,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls: type[L], value: Mapping[str, Any]) -> L:
        events = tuple(
            DomainEvent(
                event_type=item["event_type"],
                aggregate_id=Identifier(item["aggregate_id"]),
                tenant_id=Identifier(item["tenant_id"]),
                occurred_at=datetime.fromisoformat(item["occurred_at"]),
                data=item.get("data", {}),
                schema_version=item.get("schema_version", SCHEMA_VERSION),
            )
            for item in value.get("events", ())
        )
        return cls(
            id=Identifier(value["id"]),
            tenant_id=Identifier(value["tenant_id"]),
            status=cls.STATUS(value["status"]),
            version=int(value.get("version", 0)),
            events=events,
        )


def _lifecycle_type(name: str, status: type[Enum], transitions: Mapping[Enum, set[Enum]]) -> type[LifecycleAggregate]:
    namespace = {
        "__module__": __name__,
        "STATUS": status,
        "TRANSITIONS": {key: frozenset(value) for key, value in transitions.items()},
    }
    return dataclass(frozen=True)(type(name, (LifecycleAggregate,), namespace))


Quote = _lifecycle_type("Quote", QuoteStatus, {
    QuoteStatus.DRAFT: {QuoteStatus.OFFERED, QuoteStatus.CANCELLED},
    QuoteStatus.OFFERED: {QuoteStatus.ACCEPTED, QuoteStatus.EXPIRED, QuoteStatus.CANCELLED},
})
Order = _lifecycle_type("Order", OrderStatus, {
    OrderStatus.DRAFT: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.FULFILLED, OrderStatus.CANCELLED},
})
Shipment = _lifecycle_type("Shipment", ShipmentStatus, {
    ShipmentStatus.DRAFT: {ShipmentStatus.BOOKED, ShipmentStatus.CANCELLED},
    ShipmentStatus.BOOKED: {ShipmentStatus.PICKED_UP, ShipmentStatus.CANCELLED},
    ShipmentStatus.PICKED_UP: {ShipmentStatus.IN_TRANSIT},
    ShipmentStatus.IN_TRANSIT: {ShipmentStatus.DELIVERED},
})
Load = _lifecycle_type("Load", LoadStatus, {
    LoadStatus.SCHEDULED: {LoadStatus.TENDERED, LoadStatus.CANCELLED},
    LoadStatus.TENDERED: {LoadStatus.ACCEPTED, LoadStatus.CANCELLED},
    LoadStatus.ACCEPTED: {LoadStatus.DISPATCHED, LoadStatus.CANCELLED},
    LoadStatus.DISPATCHED: {LoadStatus.COMPLETED},
})
Stop = _lifecycle_type("Stop", StopStatus, {
    StopStatus.SCHEDULED: {StopStatus.ARRIVED, StopStatus.SKIPPED},
    StopStatus.ARRIVED: {StopStatus.SERVICED, StopStatus.SKIPPED},
})
Pickup = _lifecycle_type("Pickup", PickupStatus, {
    PickupStatus.SCHEDULED: {PickupStatus.ARRIVED, PickupStatus.CANCELLED},
    PickupStatus.ARRIVED: {PickupStatus.COLLECTED, PickupStatus.FAILED},
})
Delivery = _lifecycle_type("Delivery", DeliveryStatus, {
    DeliveryStatus.SCHEDULED: {DeliveryStatus.OUT_FOR_DELIVERY, DeliveryStatus.CANCELLED},
    DeliveryStatus.OUT_FOR_DELIVERY: {DeliveryStatus.DELIVERED, DeliveryStatus.FAILED},
    DeliveryStatus.FAILED: {DeliveryStatus.SCHEDULED, DeliveryStatus.CANCELLED},
})
Return = _lifecycle_type("Return", ReturnStatus, {
    ReturnStatus.REQUESTED: {ReturnStatus.APPROVED, ReturnStatus.REJECTED},
    ReturnStatus.APPROVED: {ReturnStatus.IN_TRANSIT},
    ReturnStatus.IN_TRANSIT: {ReturnStatus.RECEIVED},
})
Claim = _lifecycle_type("Claim", ClaimStatus, {
    ClaimStatus.OPEN: {ClaimStatus.UNDER_REVIEW},
    ClaimStatus.UNDER_REVIEW: {ClaimStatus.APPROVED, ClaimStatus.REJECTED},
    ClaimStatus.APPROVED: {ClaimStatus.SETTLED},
})
Incident = _lifecycle_type("Incident", IncidentStatus, {
    IncidentStatus.OPEN: {IncidentStatus.INVESTIGATING},
    IncidentStatus.INVESTIGATING: {IncidentStatus.RESOLVED},
    IncidentStatus.RESOLVED: {IncidentStatus.CLOSED, IncidentStatus.INVESTIGATING},
})

# A consignment is a shipment aggregate with an independent identifier/lifecycle.
Consignment = _lifecycle_type("Consignment", ShipmentStatus, Shipment.TRANSITIONS)


__all__ = [
    "SCHEMA_VERSION", "DomainError", "InvalidTransition", "Identifier", "GeoCoordinate",
    "Address", "Contact", "DomainEvent", "Entity", "LifecycleAggregate",
    *_ENTITY_NAMES,
    "QuoteStatus", "OrderStatus", "ShipmentStatus", "LoadStatus", "StopStatus",
    "PickupStatus", "DeliveryStatus", "ReturnStatus", "ClaimStatus", "IncidentStatus",
    "Quote", "Order", "Shipment", "Load", "Stop", "Pickup", "Delivery", "Return",
    "Claim", "Incident", "Consignment",
]
