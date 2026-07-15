"""Typed NovaRide runtime models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.geography import AddressRef, GeoPoint
from afritech.novaride_runtime.common.money import Money


SCHEMA_VERSION = "2026.2"


class ActorType(StrEnum):
    RIDER = "RIDER"
    DRIVER = "DRIVER"
    OPERATOR = "OPERATOR"
    SYSTEM = "SYSTEM"
    NOVAAI = "NOVAAI"


class BookingState(StrEnum):
    DRAFT = "DRAFT"
    QUOTED = "QUOTED"
    CONFIRMED = "CONFIRMED"
    SEARCHING = "SEARCHING"
    ASSIGNED = "ASSIGNED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    CONVERTED_TO_TRIP = "CONVERTED_TO_TRIP"


class TripState(StrEnum):
    CREATED = "CREATED"
    MATCHING = "MATCHING"
    ASSIGNED = "ASSIGNED"
    DRIVER_ACCEPTED = "DRIVER_ACCEPTED"
    DRIVER_EN_ROUTE = "DRIVER_EN_ROUTE"
    DRIVER_ARRIVED = "DRIVER_ARRIVED"
    PICKUP_VERIFIED = "PICKUP_VERIFIED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETING = "COMPLETING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EMERGENCY = "EMERGENCY"
    DISPUTED = "DISPUTED"


class DriverAvailabilityState(StrEnum):
    OFFLINE = "OFFLINE"
    STARTING_SHIFT = "STARTING_SHIFT"
    ONLINE_NOT_CONFIRMED = "ONLINE_NOT_CONFIRMED"
    AVAILABLE = "AVAILABLE"
    OFFER_RESERVED = "OFFER_RESERVED"
    EN_ROUTE_TO_PICKUP = "EN_ROUTE_TO_PICKUP"
    WAITING_AT_PICKUP = "WAITING_AT_PICKUP"
    ON_TRIP = "ON_TRIP"
    PAUSED = "PAUSED"
    BREAK_REQUIRED = "BREAK_REQUIRED"
    SUSPENDED = "SUSPENDED"


class LogisticsState(StrEnum):
    CREATED = "CREATED"
    QUOTED = "QUOTED"
    CONFIRMED = "CONFIRMED"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETURN_REQUESTED = "RETURN_REQUESTED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class EmergencyState(StrEnum):
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    TRIAGED = "TRIAGED"
    RESPONDING = "RESPONDING"
    ESCALATED = "ESCALATED"
    STABILIZED = "STABILIZED"
    RESOLVED = "RESOLVED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    CLOSED = "CLOSED"


class IncidentState(StrEnum):
    REPORTED = "REPORTED"
    TRIAGED = "TRIAGED"
    ASSIGNED = "ASSIGNED"
    INVESTIGATING = "INVESTIGATING"
    ACTION_REQUIRED = "ACTION_REQUIRED"
    RESOLVED = "RESOLVED"
    REVIEWED = "REVIEWED"
    CLOSED = "CLOSED"


class OfferState(StrEnum):
    CREATED = "CREATED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class RuntimeContext:
    tenant_id: str
    organization_id: str
    region_code: str
    actor_type: ActorType
    actor_id: str
    roles: tuple[str, ...] = ()
    device_trusted: bool = True
    session_valid: bool = True
    correlation_id: str = "corr_novaride_runtime"


@dataclass(slots=True)
class Aggregate:
    id: str
    tenant_id: str
    organization_id: str
    region_code: str
    aggregate_version: int = 1
    schema_version: str = SCHEMA_VERSION
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.aggregate_version += 1
        self.updated_at = utc_now()


@dataclass(slots=True)
class DriverProfile(Aggregate):
    identity_id: str = ""
    display_name: str = ""
    licence_reference: str | None = None
    vehicle_id: str | None = None
    app_version: str = "2026.2.0"


@dataclass(slots=True)
class DriverEligibility(Aggregate):
    driver_id: str = ""
    eligible: bool = False
    reasons: tuple[str, ...] = ()
    vehicle_compliant: bool = False
    safety_hold: bool = False
    compliance_hold: bool = False
    app_version_supported: bool = True


@dataclass(slots=True)
class DriverAvailability(Aggregate):
    driver_id: str = ""
    requested_state: DriverAvailabilityState = DriverAvailabilityState.OFFLINE
    authoritative_state: DriverAvailabilityState = DriverAvailabilityState.OFFLINE
    dispatchable: bool = False
    active_shift_id: str | None = None
    vehicle_id: str | None = None
    location_fresh: bool = False
    server_confirmed_at: datetime | None = None


@dataclass(slots=True)
class DriverShift(Aggregate):
    driver_id: str = ""
    state: str = "STARTED"
    started_at: datetime = field(default_factory=utc_now)
    ended_at: datetime | None = None


@dataclass(slots=True)
class DriverOffer(Aggregate):
    driver_id: str = ""
    trip_id: str = ""
    estimated_earnings: Money = field(default_factory=lambda: Money.of("0", "AUD"))
    state: OfferState = OfferState.CREATED
    expires_at: datetime | None = None


@dataclass(slots=True)
class DriverBid(Aggregate):
    driver_id: str = ""
    offer_id: str = ""
    amount: Money = field(default_factory=lambda: Money.of("0", "AUD"))


@dataclass(frozen=True, slots=True)
class DriverLocation:
    driver_id: str
    point: GeoPoint
    observed_at: datetime
    accuracy_m: Decimal | None = None


@dataclass(slots=True)
class DriverDiagnosticState(Aggregate):
    driver_id: str = ""
    app_version: str = "2026.2.0"
    build_id: str = "runtime-local"
    network: str = "UNKNOWN"
    gps: str = "UNKNOWN"
    offline_queue_size: int = 0


@dataclass(slots=True)
class OfflineOperation(Aggregate):
    actor_id: str = ""
    operation_type: str = ""
    payload_hash: str = ""
    idempotency_key: str = ""
    authority_required: bool = False
    status: str = "QUEUED"


@dataclass(slots=True)
class RiderProfile(Aggregate):
    identity_id: str = ""
    display_name: str = ""
    locale: str = "en"
    currency: str = "AUD"
    trust_status: str = "BASIC"


@dataclass(frozen=True, slots=True)
class JourneySearch:
    pickup: AddressRef
    destination: AddressRef
    accessibility: tuple[str, ...] = ()
    preferences: tuple[str, ...] = ()


@dataclass(slots=True)
class FareQuote(Aggregate):
    service_type: str = "economy"
    base_fare: Money = field(default_factory=lambda: Money.of("5", "AUD"))
    distance_fare: Money = field(default_factory=lambda: Money.of("10", "AUD"))
    time_fare: Money = field(default_factory=lambda: Money.of("3", "AUD"))
    taxes: Money = field(default_factory=lambda: Money.of("1.80", "AUD"))
    tolls: Money = field(default_factory=lambda: Money.of("0", "AUD"))
    local_fees: Money = field(default_factory=lambda: Money.of("0", "AUD"))
    surge: Money = field(default_factory=lambda: Money.of("0", "AUD"))
    discounts: Money = field(default_factory=lambda: Money.of("0", "AUD"))
    estimated_total: Money = field(default_factory=lambda: Money.of("19.80", "AUD"))
    pricing_policy_version: str = "pricing-policy-2026.2"
    payment_methods: tuple[str, ...] = ("NovaPay Wallet", "Cash")
    expires_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class BookingIntent:
    rider_id: str
    pickup: AddressRef
    destination: AddressRef
    service_type: str
    payment_preference: str = "NovaPay Wallet"


@dataclass(slots=True)
class Booking(Aggregate):
    rider_id: str = ""
    pickup: AddressRef | None = None
    destination: AddressRef | None = None
    service_type: str = "economy"
    state: BookingState = BookingState.DRAFT
    fare_quote_id: str | None = None
    trip_id: str | None = None


RiderBooking = Booking


@dataclass(slots=True)
class Trip(Aggregate):
    booking_id: str = ""
    rider_id: str = ""
    driver_id: str | None = None
    vehicle_id: str | None = None
    service_type: str = "economy"
    pickup: AddressRef | None = None
    destination: AddressRef | None = None
    fare_reference: str | None = None
    payment_reference: str | None = None
    safety_state: str = "NORMAL"
    lifecycle_state: TripState = TripState.CREATED
    evidence_reference: str | None = None


@dataclass(slots=True)
class TripShare(Aggregate):
    trip_id: str = ""
    recipient: str = ""


@dataclass(slots=True)
class RiderEmergencyRequest(Aggregate):
    rider_id: str = ""
    trip_id: str | None = None
    state: EmergencyState = EmergencyState.TRIGGERED
    visible_reference: str = ""


@dataclass(slots=True)
class Rating(Aggregate):
    trip_id: str = ""
    score: int = 5
    comment: str | None = None


@dataclass(slots=True)
class SupportCase(Aggregate):
    subject_id: str = ""
    case_type: str = "GENERAL"
    status: str = "OPEN"


@dataclass(frozen=True, slots=True)
class OperatorIdentity:
    operator_id: str
    roles: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OperatorAuthority:
    can_intervene: bool
    four_eyes_required: bool = False
    approval_reference: str | None = None


@dataclass(slots=True)
class OperatorCommand(Aggregate):
    command_type: str = ""
    target_id: str = ""
    reason: str = ""
    authority_decision: str = "PENDING"
    evidence_reference: str | None = None


@dataclass(slots=True)
class OperatorIntervention(Aggregate):
    command_id: str = ""
    before_state: dict[str, Any] = field(default_factory=dict)
    intended_transition: str = ""


@dataclass(slots=True)
class EmergencyCase(Aggregate):
    source: ActorType = ActorType.RIDER
    source_id: str = ""
    trip_id: str | None = None
    state: EmergencyState = EmergencyState.TRIGGERED
    evidence_locked: bool = False
    visible_reference: str = ""


@dataclass(slots=True)
class Incident(Aggregate):
    category: str = "Safety"
    state: IncidentState = IncidentState.REPORTED
    severity: str = "MEDIUM"
    owner_id: str | None = None


@dataclass(slots=True)
class Escalation(Aggregate):
    incident_id: str = ""
    target_team: str = ""


@dataclass(slots=True)
class ApprovalRecord(Aggregate):
    subject_id: str = ""
    status: str = "PENDING"
    required_quorum: int = 2
    votes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DispatchRequest:
    booking_id: str
    rider_id: str
    region_code: str
    service_type: str


@dataclass(frozen=True, slots=True)
class DispatchCandidate:
    driver_id: str
    score: Decimal
    reasons: tuple[str, ...]


@dataclass(slots=True)
class DispatchOffer(Aggregate):
    driver_id: str = ""
    booking_id: str = ""
    trip_id: str = ""
    state: OfferState = OfferState.CREATED


@dataclass(slots=True)
class Assignment(Aggregate):
    trip_id: str = ""
    driver_id: str = ""
    vehicle_id: str | None = None


@dataclass(frozen=True, slots=True)
class RoutePlan:
    route_id: str
    legs: tuple[dict[str, Any], ...]
    distance_km: Decimal
    duration_minutes: int


Fare = FareQuote


@dataclass(frozen=True, slots=True)
class PricingPolicy:
    policy_id: str
    region_code: str
    currency: str
    surge_enabled: bool


@dataclass(frozen=True, slots=True)
class SafetyState:
    status: str
    signals: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Geofence:
    geofence_id: str
    region_code: str
    kind: str


@dataclass(frozen=True, slots=True)
class RegionPolicy:
    region_code: str
    currencies: tuple[str, ...]
    languages: tuple[str, ...]
    service_types: tuple[str, ...]
    cash_available: bool
    mobile_money_methods: tuple[str, ...]
    real_payments_enabled: bool = False
    ga_allowed: bool = False


@dataclass(frozen=True, slots=True)
class FeatureActivation:
    feature: str
    enabled: bool
    region_code: str


@dataclass(slots=True)
class Fleet(Aggregate):
    name: str = ""
    status: str = "ACTIVE"


@dataclass(slots=True)
class FleetDriver(Aggregate):
    fleet_id: str = ""
    driver_id: str = ""
    status: str = "ACTIVE"


@dataclass(slots=True)
class FleetVehicle(Aggregate):
    fleet_id: str = ""
    vehicle_id: str = ""
    compliant: bool = True
    fuel_or_ev_state: str = "UNKNOWN"


@dataclass(slots=True)
class FleetShift(Aggregate):
    fleet_id: str = ""
    driver_id: str = ""


FleetSchedule = FleetShift


@dataclass(slots=True)
class FleetComplianceState(Aggregate):
    fleet_id: str = ""
    compliance_hold: bool = False
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FleetRevenueSummary:
    fleet_id: str
    revenue_reference: str


@dataclass(slots=True)
class DeliveryOrder(Aggregate):
    sender_id: str = ""
    recipient_name: str = ""
    pickup: AddressRef | None = None
    dropoff: AddressRef | None = None
    package_metadata: dict[str, Any] = field(default_factory=dict)
    state: LogisticsState = LogisticsState.CREATED
    chain_of_custody: tuple[str, ...] = ()


@dataclass(slots=True)
class DeliveryAssignment(Aggregate):
    order_id: str = ""
    driver_id: str = ""


@dataclass(slots=True)
class DeliveryStop(Aggregate):
    order_id: str = ""
    stop_type: str = "PICKUP"
    address: AddressRef | None = None


@dataclass(slots=True)
class ChainOfCustody(Aggregate):
    order_id: str = ""
    entries: tuple[str, ...] = ()


@dataclass(slots=True)
class DeliveryEvidence(Aggregate):
    order_id: str = ""
    evidence_reference: str = ""


@dataclass(slots=True)
class ReturnRequest(Aggregate):
    order_id: str = ""
    reason: str = ""


@dataclass(slots=True)
class CorporateAccount(Aggregate):
    name: str = ""
    wallet_reference: str | None = None


@dataclass(slots=True)
class EmployeeProfile(Aggregate):
    account_id: str = ""
    identity_id: str = ""
    cost_center_id: str | None = None


@dataclass(slots=True)
class TravelPolicy(Aggregate):
    account_id: str = ""
    allowed_ride_classes: tuple[str, ...] = ("economy",)
    approval_required: bool = False
    spending_limit: Money = field(default_factory=lambda: Money.of("100", "AUD"))


@dataclass(slots=True)
class CostCenter(Aggregate):
    account_id: str = ""
    code: str = ""


@dataclass(slots=True)
class CorporateBooking(Aggregate):
    account_id: str = ""
    employee_id: str = ""
    booking_id: str = ""
    cost_center_id: str | None = None


@dataclass(frozen=True, slots=True)
class InvoiceReference:
    invoice_id: str
    account_id: str


@dataclass(frozen=True, slots=True)
class ExpenseRecord:
    expense_id: str
    account_id: str
    booking_id: str


@dataclass(slots=True)
class TransitStop(Aggregate):
    name: str = ""
    point: GeoPoint | None = None


@dataclass(slots=True)
class TransitRoute(Aggregate):
    route_name: str = ""
    mode: str = "BUS"


@dataclass(frozen=True, slots=True)
class TransitLeg:
    mode: str
    from_label: str
    to_label: str
    provider: str = "provider_neutral"


@dataclass(slots=True)
class TransitJourney(Aggregate):
    rider_id: str = ""
    legs: tuple[TransitLeg, ...] = ()
    first_mile_booking_id: str | None = None
    last_mile_booking_id: str | None = None


@dataclass(slots=True)
class ServiceAlert(Aggregate):
    route_id: str = ""
    message: str = ""


@dataclass(frozen=True, slots=True)
class MobilityConnection:
    from_mode: str
    to_mode: str
    description: str


@dataclass(frozen=True, slots=True)
class WalletReference:
    wallet_id: str
    provider: str = "NovaPay"


@dataclass(frozen=True, slots=True)
class PaymentIntentReference:
    payment_intent_id: str
    provider: str = "NovaPay"
    real_payment_enabled: bool = False


@dataclass(frozen=True, slots=True)
class SettlementReference:
    settlement_id: str
    provider: str = "NovaPay"


@dataclass(frozen=True, slots=True)
class PayoutReference:
    payout_id: str
    provider: str = "NovaPay"


@dataclass(frozen=True, slots=True)
class RefundReference:
    refund_id: str
    provider: str = "NovaPay"


@dataclass(frozen=True, slots=True)
class FinancialProductReference:
    product_id: str
    product_type: str
    provider: str = "NovaPay"
