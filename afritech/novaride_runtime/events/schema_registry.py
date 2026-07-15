"""NovaRide event schema registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from afritech.novaride_runtime.events.registry import REQUIRED_EVENTS


@dataclass(frozen=True, slots=True)
class EventSchema:
    event_type: str
    schema_version: str
    aggregate_type: str
    required_payload_fields: tuple[str, ...] = ()
    compatibility: str = "BACKWARD_COMPATIBLE_ADDITIVE"
    migration: Callable[[dict[str, Any]], dict[str, Any]] | None = None


@dataclass(slots=True)
class EventSchemaRegistry:
    schemas: dict[tuple[str, str], EventSchema] = field(default_factory=dict)

    def register(self, schema: EventSchema) -> None:
        self.schemas[(schema.event_type, schema.schema_version)] = schema

    def get(self, event_type: str, schema_version: str) -> EventSchema | None:
        return self.schemas.get((event_type, schema_version))

    def validate_payload(self, event_type: str, schema_version: str, payload: dict[str, Any]) -> tuple[bool, tuple[str, ...]]:
        schema = self.get(event_type, schema_version)
        if schema is None:
            return False, ("unsupported_schema_version",)
        missing = tuple(field for field in schema.required_payload_fields if field not in payload)
        return not missing, missing


def default_event_schema_registry() -> EventSchemaRegistry:
    registry = EventSchemaRegistry()
    aggregate_overrides = {
        "FareQuoted": "FareQuote",
        "BookingCreated": "Booking",
        "BookingConfirmed": "Booking",
        "DriverAssigned": "Trip",
        "DriverOfferCreated": "DriverOffer",
        "DriverOfferAccepted": "DriverOffer",
        "TripCompleted": "Trip",
        "TripEvidenceFinalized": "Trip",
        "EmergencyActivated": "EmergencyCase",
        "EmergencyAcknowledged": "EmergencyCase",
        "FleetVehicleAssigned": "FleetVehicle",
        "DeliveryCreated": "DeliveryOrder",
        "DeliveryPickedUp": "DeliveryOrder",
        "DeliveryCompleted": "DeliveryOrder",
        "CorporateBookingCreated": "CorporateBooking",
        "TransitJourneyPlanned": "TransitJourney",
    }
    for event_type in REQUIRED_EVENTS + ("DriverAvailable", "DriverEnRoute", "TripCompleting", "DeliveryFailed", "DeliveryReturned", "DriverRebalanceRecommended"):
        registry.register(
            EventSchema(
                event_type=event_type,
                schema_version="2026.2",
                aggregate_type=aggregate_overrides.get(event_type, "MobilityAggregate"),
            )
        )
    return registry
