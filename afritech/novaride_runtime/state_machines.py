"""Validated NovaRide state machines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from afritech.novaride_runtime.common.errors import InvalidTransition
from afritech.novaride_runtime.models import (
    ActorType,
    BookingState,
    DriverAvailabilityState,
    EmergencyState,
    IncidentState,
    LogisticsState,
    TripState,
)


class Authority(StrEnum):
    RIDER = "RIDER"
    DRIVER = "DRIVER"
    OPERATOR = "OPERATOR"
    CORE = "CORE"
    POLICY = "POLICY"
    SYSTEM = "SYSTEM"


@dataclass(frozen=True, slots=True)
class TransitionRule:
    source: StrEnum
    target: StrEnum
    actor_types: tuple[ActorType, ...]
    authority: Authority
    required_evidence: tuple[str, ...]
    required_policy_checks: tuple[str, ...]
    emitted_events: tuple[str, ...]
    idempotency_behavior: str = "return_existing_result"
    concurrency_behavior: str = "optimistic_aggregate_version"
    rejection_reason: str = "transition_not_allowed"


BOOKING_TRANSITIONS: tuple[TransitionRule, ...] = (
    TransitionRule(
        BookingState.DRAFT,
        BookingState.QUOTED,
        (ActorType.RIDER, ActorType.SYSTEM),
        Authority.CORE,
        (),
        ("region_enabled",),
        ("FareQuoted",),
    ),
    TransitionRule(
        BookingState.QUOTED,
        BookingState.CONFIRMED,
        (ActorType.RIDER,),
        Authority.CORE,
        (),
        ("payment_method_allowed",),
        ("BookingConfirmed",),
    ),
    TransitionRule(
        BookingState.CONFIRMED,
        BookingState.SEARCHING,
        (ActorType.SYSTEM,),
        Authority.CORE,
        (),
        ("dispatch_enabled",),
        ("DriverSearchStarted",),
    ),
    TransitionRule(
        BookingState.SEARCHING,
        BookingState.ASSIGNED,
        (ActorType.SYSTEM,),
        Authority.CORE,
        (),
        ("driver_eligible",),
        ("DriverAssigned",),
    ),
    TransitionRule(
        BookingState.ASSIGNED,
        BookingState.CONVERTED_TO_TRIP,
        (ActorType.SYSTEM,),
        Authority.CORE,
        ("assignment",),
        ("trip_creation_allowed",),
        ("BookingConvertedToTrip",),
    ),
    TransitionRule(
        BookingState.QUOTED,
        BookingState.CANCELLED,
        (ActorType.RIDER, ActorType.OPERATOR),
        Authority.CORE,
        (),
        ("cancellation_allowed",),
        ("BookingCancelled",),
    ),
    TransitionRule(
        BookingState.CONFIRMED,
        BookingState.CANCELLED,
        (ActorType.RIDER, ActorType.OPERATOR),
        Authority.CORE,
        (),
        ("cancellation_allowed",),
        ("BookingCancelled",),
    ),
)

TRIP_TRANSITIONS: tuple[TransitionRule, ...] = (
    TransitionRule(
        TripState.CREATED,
        TripState.MATCHING,
        (ActorType.SYSTEM,),
        Authority.CORE,
        (),
        ("dispatch_enabled",),
        ("DriverSearchStarted",),
    ),
    TransitionRule(
        TripState.MATCHING,
        TripState.ASSIGNED,
        (ActorType.SYSTEM,),
        Authority.CORE,
        (),
        ("driver_eligible",),
        ("DriverAssigned",),
    ),
    TransitionRule(
        TripState.ASSIGNED,
        TripState.DRIVER_ACCEPTED,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("offer_active",),
        ("DriverOfferAccepted",),
    ),
    TransitionRule(
        TripState.DRIVER_ACCEPTED,
        TripState.DRIVER_EN_ROUTE,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("location_fresh",),
        ("DriverEnRoute",),
    ),
    TransitionRule(
        TripState.DRIVER_EN_ROUTE,
        TripState.DRIVER_ARRIVED,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("arrival_radius",),
        ("DriverArrived",),
    ),
    TransitionRule(
        TripState.DRIVER_ARRIVED,
        TripState.PICKUP_VERIFIED,
        (ActorType.DRIVER,),
        Authority.CORE,
        ("pickup_pin_or_qr",),
        ("pickup_verification",),
        ("PickupVerified",),
    ),
    TransitionRule(
        TripState.PICKUP_VERIFIED,
        TripState.IN_PROGRESS,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("trip_start_allowed",),
        ("TripStarted",),
    ),
    TransitionRule(
        TripState.IN_PROGRESS,
        TripState.COMPLETING,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("destination_reached",),
        ("TripCompleting",),
    ),
    TransitionRule(
        TripState.COMPLETING,
        TripState.COMPLETED,
        (ActorType.DRIVER, ActorType.SYSTEM),
        Authority.CORE,
        ("trip_summary",),
        ("payment_reference_created",),
        ("TripCompleted", "PaymentRequested"),
    ),
    TransitionRule(
        TripState.IN_PROGRESS,
        TripState.EMERGENCY,
        (ActorType.RIDER, ActorType.DRIVER, ActorType.OPERATOR),
        Authority.CORE,
        ("emergency_context",),
        ("safety_enabled",),
        ("EmergencyActivated",),
    ),
    TransitionRule(
        TripState.CREATED,
        TripState.CANCELLED,
        (ActorType.RIDER, ActorType.OPERATOR),
        Authority.CORE,
        (),
        ("cancellation_allowed",),
        ("TripCancelled",),
    ),
    TransitionRule(
        TripState.ASSIGNED,
        TripState.CANCELLED,
        (ActorType.RIDER, ActorType.OPERATOR),
        Authority.CORE,
        (),
        ("cancellation_allowed",),
        ("TripCancelled",),
    ),
)

DRIVER_AVAILABILITY_TRANSITIONS: tuple[TransitionRule, ...] = (
    TransitionRule(
        DriverAvailabilityState.OFFLINE,
        DriverAvailabilityState.STARTING_SHIFT,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("session_valid",),
        ("DriverShiftStarting",),
    ),
    TransitionRule(
        DriverAvailabilityState.STARTING_SHIFT,
        DriverAvailabilityState.ONLINE_NOT_CONFIRMED,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("eligibility_checked",),
        ("DriverOnlineRequested",),
    ),
    TransitionRule(
        DriverAvailabilityState.ONLINE_NOT_CONFIRMED,
        DriverAvailabilityState.AVAILABLE,
        (ActorType.SYSTEM,),
        Authority.CORE,
        ("supply_registration",),
        ("dispatchable",),
        ("DriverAvailable",),
    ),
    TransitionRule(
        DriverAvailabilityState.AVAILABLE,
        DriverAvailabilityState.OFFER_RESERVED,
        (ActorType.SYSTEM,),
        Authority.CORE,
        (),
        ("offer_created",),
        ("DriverOfferCreated",),
    ),
    TransitionRule(
        DriverAvailabilityState.OFFER_RESERVED,
        DriverAvailabilityState.EN_ROUTE_TO_PICKUP,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("offer_accepted",),
        ("DriverOfferAccepted",),
    ),
    TransitionRule(
        DriverAvailabilityState.EN_ROUTE_TO_PICKUP,
        DriverAvailabilityState.WAITING_AT_PICKUP,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("arrival_radius",),
        ("DriverArrived",),
    ),
    TransitionRule(
        DriverAvailabilityState.WAITING_AT_PICKUP,
        DriverAvailabilityState.ON_TRIP,
        (ActorType.DRIVER,),
        Authority.CORE,
        ("pickup_pin_or_qr",),
        ("pickup_verification",),
        ("TripStarted",),
    ),
    TransitionRule(
        DriverAvailabilityState.ON_TRIP,
        DriverAvailabilityState.AVAILABLE,
        (ActorType.DRIVER, ActorType.SYSTEM),
        Authority.CORE,
        ("trip_completion",),
        ("trip_completed",),
        ("DriverAvailable",),
    ),
    TransitionRule(
        DriverAvailabilityState.AVAILABLE,
        DriverAvailabilityState.PAUSED,
        (ActorType.DRIVER, ActorType.OPERATOR),
        Authority.CORE,
        (),
        ("pause_allowed",),
        ("DriverPaused",),
    ),
    TransitionRule(
        DriverAvailabilityState.PAUSED,
        DriverAvailabilityState.AVAILABLE,
        (ActorType.DRIVER, ActorType.OPERATOR),
        Authority.CORE,
        (),
        ("resume_allowed",),
        ("DriverAvailable",),
    ),
)

LOGISTICS_TRANSITIONS: tuple[TransitionRule, ...] = (
    TransitionRule(
        LogisticsState.CREATED,
        LogisticsState.QUOTED,
        (ActorType.RIDER, ActorType.SYSTEM),
        Authority.CORE,
        (),
        ("logistics_enabled",),
        ("DeliveryQuoted",),
    ),
    TransitionRule(
        LogisticsState.QUOTED,
        LogisticsState.CONFIRMED,
        (ActorType.RIDER,),
        Authority.CORE,
        (),
        ("restricted_items_checked",),
        ("DeliveryCreated",),
    ),
    TransitionRule(
        LogisticsState.CONFIRMED,
        LogisticsState.ASSIGNED,
        (ActorType.SYSTEM,),
        Authority.CORE,
        (),
        ("driver_vehicle_suitable",),
        ("DeliveryAssigned",),
    ),
    TransitionRule(
        LogisticsState.ASSIGNED,
        LogisticsState.PICKED_UP,
        (ActorType.DRIVER,),
        Authority.CORE,
        ("pickup_pin_or_qr",),
        ("pickup_allowed",),
        ("DeliveryPickedUp",),
    ),
    TransitionRule(
        LogisticsState.PICKED_UP,
        LogisticsState.IN_TRANSIT,
        (ActorType.DRIVER,),
        Authority.CORE,
        (),
        ("custody_valid",),
        ("DeliveryInTransit",),
    ),
    TransitionRule(
        LogisticsState.IN_TRANSIT,
        LogisticsState.DELIVERED,
        (ActorType.DRIVER,),
        Authority.CORE,
        ("delivery_pin_or_qr",),
        ("delivery_allowed",),
        ("DeliveryCompleted",),
    ),
    TransitionRule(
        LogisticsState.IN_TRANSIT,
        LogisticsState.FAILED,
        (ActorType.DRIVER, ActorType.OPERATOR),
        Authority.CORE,
        ("failure_reason",),
        ("failure_allowed",),
        ("DeliveryFailed",),
    ),
    TransitionRule(
        LogisticsState.FAILED,
        LogisticsState.RETURN_REQUESTED,
        (ActorType.OPERATOR, ActorType.SYSTEM),
        Authority.CORE,
        (),
        ("return_allowed",),
        ("DeliveryReturnRequested",),
    ),
    TransitionRule(
        LogisticsState.RETURN_REQUESTED,
        LogisticsState.RETURNED,
        (ActorType.DRIVER,),
        Authority.CORE,
        ("return_evidence",),
        ("return_allowed",),
        ("DeliveryReturned",),
    ),
)

EMERGENCY_TRANSITIONS: tuple[TransitionRule, ...] = (
    TransitionRule(
        EmergencyState.TRIGGERED,
        EmergencyState.ACKNOWLEDGED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("operator_ack",),
        ("operator_authorized",),
        ("EmergencyAcknowledged",),
    ),
    TransitionRule(
        EmergencyState.ACKNOWLEDGED,
        EmergencyState.TRIAGED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("operator_authorized",),
        ("EmergencyTriaged",),
    ),
    TransitionRule(
        EmergencyState.TRIAGED,
        EmergencyState.RESPONDING,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("operator_authorized",),
        ("EmergencyResponding",),
    ),
    TransitionRule(
        EmergencyState.RESPONDING,
        EmergencyState.ESCALATED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("escalation_reason",),
        ("operator_authorized",),
        ("EmergencyEscalated",),
    ),
    TransitionRule(
        EmergencyState.RESPONDING,
        EmergencyState.STABILIZED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("welfare_update",),
        ("operator_authorized",),
        ("EmergencyStabilized",),
    ),
    TransitionRule(
        EmergencyState.STABILIZED,
        EmergencyState.RESOLVED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("resolution_evidence",),
        ("four_eyes_if_required",),
        ("EmergencyResolved",),
    ),
    TransitionRule(
        EmergencyState.RESOLVED,
        EmergencyState.REVIEW_REQUIRED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("post_incident_review",),
        ("EmergencyReviewRequired",),
    ),
    TransitionRule(
        EmergencyState.REVIEW_REQUIRED,
        EmergencyState.CLOSED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("review_complete",),
        ("closure_allowed",),
        ("EmergencyClosed",),
    ),
)

INCIDENT_TRANSITIONS: tuple[TransitionRule, ...] = (
    TransitionRule(
        IncidentState.REPORTED,
        IncidentState.TRIAGED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("operator_authorized",),
        ("IncidentTriaged",),
    ),
    TransitionRule(
        IncidentState.TRIAGED,
        IncidentState.ASSIGNED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("owner_assigned",),
        ("IncidentAssigned",),
    ),
    TransitionRule(
        IncidentState.ASSIGNED,
        IncidentState.INVESTIGATING,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("operator_authorized",),
        ("IncidentInvestigating",),
    ),
    TransitionRule(
        IncidentState.INVESTIGATING,
        IncidentState.ACTION_REQUIRED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        (),
        ("action_required",),
        ("IncidentActionRequired",),
    ),
    TransitionRule(
        IncidentState.ACTION_REQUIRED,
        IncidentState.RESOLVED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("resolution",),
        ("resolution_allowed",),
        ("IncidentResolved",),
    ),
    TransitionRule(
        IncidentState.RESOLVED,
        IncidentState.REVIEWED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("review",),
        ("review_allowed",),
        ("IncidentReviewed",),
    ),
    TransitionRule(
        IncidentState.REVIEWED,
        IncidentState.CLOSED,
        (ActorType.OPERATOR,),
        Authority.OPERATOR,
        ("closure",),
        ("closure_allowed",),
        ("IncidentClosed",),
    ),
)


def transition_rule(source: StrEnum, target: StrEnum, actor_type: ActorType) -> TransitionRule:
    for rule in (
        BOOKING_TRANSITIONS
        + TRIP_TRANSITIONS
        + DRIVER_AVAILABILITY_TRANSITIONS
        + LOGISTICS_TRANSITIONS
        + EMERGENCY_TRANSITIONS
        + INCIDENT_TRANSITIONS
    ):
        if rule.source == source and rule.target == target and actor_type in rule.actor_types:
            return rule
    raise InvalidTransition(f"{source}->{target}:{actor_type}")
