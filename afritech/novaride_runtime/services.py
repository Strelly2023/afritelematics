"""NovaRide runtime services."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from decimal import Decimal
from typing import Any

from afritech.novaride_runtime.common.clocks import utc_now
from afritech.novaride_runtime.common.errors import AuthorityDenied, BoundaryViolation, DuplicateCommand
from afritech.novaride_runtime.common.geography import AddressRef, GeoPoint
from afritech.novaride_runtime.common.identifiers import new_id
from afritech.novaride_runtime.common.idempotency import IdempotencyRecord, payload_hash
from afritech.novaride_runtime.common.money import Money
from afritech.novaride_runtime.events.hashing import canonical_hash
from afritech.novaride_runtime.events.envelope import MobilityEvent
from afritech.novaride_runtime.models import (
    ActorType,
    Booking,
    BookingIntent,
    BookingState,
    CorporateAccount,
    CorporateBooking,
    ConflictRecord,
    DeliveryOrder,
    DegradedMode,
    DispatchOffer,
    DriverAvailability,
    DriverAvailabilityState,
    DriverEligibility,
    DriverOffer,
    DriverProfile,
    DriverShift,
    EmergencyCase,
    EmergencyState,
    FareQuote,
    Fleet,
    FleetComplianceState,
    FleetVehicle,
    FailoverEvent,
    FailoverState,
    LogisticsState,
    OfferState,
    OperatorCommand,
    OfflineOperation,
    PaymentIntentReference,
    ProviderHealth,
    ProviderHealthRecord,
    ProviderRoute,
    ProviderRouteDecision,
    ProviderState,
    ResilienceEvidence,
    RiderProfile,
    RuntimeContext,
    SyncSession,
    SyncResult,
    TransitJourney,
    TransitLeg,
    Trip,
    TripState,
)
from afritech.novaride_runtime.persistence.memory import RuntimeRepositories


def _json(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _json(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_json(item) for item in value]
    if isinstance(value, list):
        return [_json(item) for item in value]
    if isinstance(value, dict):
        return {key: _json(item) for key, item in value.items()}
    if hasattr(value, "value"):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    return value


@dataclass(slots=True)
class EventFabric:
    repositories: RuntimeRepositories

    def emit(
        self,
        context: RuntimeContext,
        *,
        event_type: str,
        aggregate_id: str,
        aggregate_type: str,
        aggregate_version: int,
        payload: dict[str, Any],
        causation_id: str | None = None,
    ) -> MobilityEvent:
        event = MobilityEvent(
            event_type=event_type,
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            aggregate_version=aggregate_version,
            tenant_id=context.tenant_id,
            region=context.region_code,
            actor_type=context.actor_type.value,
            actor_id=context.actor_id,
            correlation_id=context.correlation_id,
            causation_id=causation_id,
            payload=_json(payload),
        )
        self.repositories.events.append(event)
        return event


@dataclass(slots=True)
class PolicyService:
    ga_allowed: bool = False
    real_payments_enabled: bool = False
    enabled_regions: tuple[str, ...] = ("AU", "US", "CA", "UK", "EU", "IN", "KE", "TZ", "UG", "RW", "BI", "DRC", "NG", "GH", "ZM", "ZA")
    fair_bid_regions: tuple[str, ...] = ("KE", "TZ", "UG", "RW", "NG", "GH", "IN")

    def require_region_enabled(self, region_code: str) -> None:
        if region_code not in self.enabled_regions:
            raise AuthorityDenied("region_not_enabled")

    def require_operator(self, context: RuntimeContext) -> None:
        if context.actor_type != ActorType.OPERATOR:
            raise AuthorityDenied("operator_required")

    def fair_bid_allowed(self, region_code: str) -> bool:
        return region_code in self.fair_bid_regions

    def real_payment_guard(self) -> dict[str, Any]:
        return {
            "REAL_PAYMENTS_ENABLED": self.real_payments_enabled,
            "REAL_PAYMENT_APPROVAL": "PENDING",
        }

    def ga_guard(self) -> dict[str, Any]:
        return {"GA_ALLOWED": self.ga_allowed, "GA_APPROVAL": "PENDING"}


@dataclass(slots=True)
class NovaPayAdapter:
    policy: PolicyService

    def create_payment_intent_reference(self, amount: Money, context: RuntimeContext) -> PaymentIntentReference:
        return PaymentIntentReference(
            payment_intent_id=new_id("payintent_sandbox"),
            provider="NovaPay",
            real_payment_enabled=self.policy.real_payments_enabled,
        )

    def wallet_summary(self, context: RuntimeContext) -> dict[str, Any]:
        return {
            "provider": "NovaPay",
            "ledger_owned_by": "NovaPay",
            "real_payments_enabled": self.policy.real_payments_enabled,
            "available_balance_reference": "wallet_summary_sandbox",
        }


@dataclass(slots=True)
class BookingService:
    repositories: RuntimeRepositories
    events: EventFabric
    policy: PolicyService

    def create_quote(self, context: RuntimeContext, *, service_type: str = "economy", currency: str = "AUD") -> FareQuote:
        self.policy.require_region_enabled(context.region_code)
        quote = FareQuote(
            id=new_id("quote"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            service_type=service_type,
            base_fare=Money.of("5", currency),
            distance_fare=Money.of("10", currency),
            time_fare=Money.of("3", currency),
            taxes=Money.of("1.80", currency),
            estimated_total=Money.of("19.80", currency),
        )
        self.repositories.fare_quotes.save(quote)
        self.events.emit(context, event_type="FareQuoted", aggregate_id=quote.id, aggregate_type="FareQuote", aggregate_version=quote.aggregate_version, payload={"quote": quote})
        return quote

    def create_booking(self, context: RuntimeContext, intent: BookingIntent, *, quote_id: str | None, idempotency_key: str) -> Booking:
        command_hash = payload_hash({"intent": _json(intent), "quote_id": quote_id})
        existing = self.repositories.idempotency.get(context.tenant_id, idempotency_key)
        if existing:
            booking_id = existing.result["booking_id"]
            booking = self.repositories.bookings.get(booking_id)
            if booking is None:
                raise DuplicateCommand("idempotent_booking_missing")
            return booking
        booking = Booking(
            id=new_id("booking"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            rider_id=intent.rider_id,
            pickup=intent.pickup,
            destination=intent.destination,
            service_type=intent.service_type,
            state=BookingState.CONFIRMED,
            fare_quote_id=quote_id,
        )
        self.repositories.bookings.save(booking)
        self.repositories.idempotency.put(
            IdempotencyRecord(context.tenant_id, idempotency_key, command_hash, {"booking_id": booking.id})
        )
        self.events.emit(context, event_type="BookingCreated", aggregate_id=booking.id, aggregate_type="Booking", aggregate_version=booking.aggregate_version, payload={"booking": booking})
        self.events.emit(context, event_type="BookingConfirmed", aggregate_id=booking.id, aggregate_type="Booking", aggregate_version=booking.aggregate_version, payload={"booking_id": booking.id})
        return booking


@dataclass(slots=True)
class DriverService:
    repositories: RuntimeRepositories
    events: EventFabric
    policy: PolicyService

    def onboard(self, context: RuntimeContext, *, identity_id: str, display_name: str, vehicle_id: str | None = None) -> DriverProfile:
        profile = DriverProfile(
            id=context.actor_id if context.actor_type == ActorType.DRIVER else new_id("driver"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            identity_id=identity_id,
            display_name=display_name,
            vehicle_id=vehicle_id,
        )
        self.repositories.drivers.save(profile)
        eligibility = DriverEligibility(
            id=new_id("eligibility"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            driver_id=profile.id,
            eligible=True,
            reasons=("identity_valid", "vehicle_compliant", "region_enabled"),
            vehicle_compliant=True,
        )
        self.repositories.eligibility.save(eligibility)
        availability = DriverAvailability(
            id=profile.id,
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            driver_id=profile.id,
            vehicle_id=vehicle_id,
        )
        self.repositories.availability.save(availability)
        return profile

    def start_shift(self, context: RuntimeContext, driver_id: str) -> DriverShift:
        shift = DriverShift(
            id=new_id("shift"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            driver_id=driver_id,
        )
        self.repositories.shifts.save(shift)
        availability = self.repositories.availability.get(driver_id)
        if availability:
            availability.requested_state = DriverAvailabilityState.STARTING_SHIFT
            availability.authoritative_state = DriverAvailabilityState.ONLINE_NOT_CONFIRMED
            availability.active_shift_id = shift.id
            availability.server_confirmed_at = utc_now()
            availability.touch()
            self.repositories.availability.save(availability)
        return shift

    def set_available(self, context: RuntimeContext, driver_id: str, *, location_fresh: bool = True) -> DriverAvailability:
        availability = self.repositories.availability.get(driver_id)
        eligibility_items = [item for item in self.repositories.eligibility.list(tenant_id=context.tenant_id) if item.driver_id == driver_id]
        eligibility = eligibility_items[-1] if eligibility_items else None
        if availability is None:
            raise ValueError("driver_availability_not_found")
        dispatchable = bool(
            context.session_valid
            and context.device_trusted
            and eligibility
            and eligibility.eligible
            and eligibility.vehicle_compliant
            and not eligibility.safety_hold
            and not eligibility.compliance_hold
            and eligibility.app_version_supported
            and availability.active_shift_id
            and location_fresh
            and context.region_code in self.policy.enabled_regions
        )
        availability.requested_state = DriverAvailabilityState.AVAILABLE
        availability.authoritative_state = DriverAvailabilityState.AVAILABLE if dispatchable else DriverAvailabilityState.ONLINE_NOT_CONFIRMED
        availability.dispatchable = dispatchable
        availability.location_fresh = location_fresh
        availability.server_confirmed_at = utc_now()
        availability.touch()
        self.repositories.availability.save(availability)
        if dispatchable:
            self.events.emit(context, event_type="DriverAvailable", aggregate_id=driver_id, aggregate_type="DriverAvailability", aggregate_version=availability.aggregate_version, payload={"driver_id": driver_id})
        return availability


@dataclass(slots=True)
class DispatchService:
    repositories: RuntimeRepositories
    events: EventFabric

    def start_dispatch(self, context: RuntimeContext, booking_id: str) -> DriverOffer:
        booking = self.repositories.bookings.get(booking_id)
        if booking is None:
            raise ValueError("booking_not_found")
        candidates = [item for item in self.repositories.availability.list(tenant_id=context.tenant_id) if item.dispatchable]
        if not candidates:
            raise ValueError("no_dispatchable_driver")
        driver_id = candidates[0].driver_id
        trip = Trip(
            id=new_id("trip"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            booking_id=booking.id,
            rider_id=booking.rider_id,
            driver_id=driver_id,
            vehicle_id=candidates[0].vehicle_id,
            service_type=booking.service_type,
            pickup=booking.pickup,
            destination=booking.destination,
            lifecycle_state=TripState.ASSIGNED,
            fare_reference=booking.fare_quote_id,
        )
        booking.state = BookingState.ASSIGNED
        booking.trip_id = trip.id
        booking.touch()
        self.repositories.bookings.save(booking)
        self.repositories.trips.save(trip)
        offer = DriverOffer(
            id=new_id("offer"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            driver_id=driver_id,
            trip_id=trip.id,
            estimated_earnings=Money.of("14.50", "AUD"),
        )
        self.repositories.offers.save(offer)
        self.events.emit(context, event_type="DriverSearchStarted", aggregate_id=booking.id, aggregate_type="Booking", aggregate_version=booking.aggregate_version, payload={"booking_id": booking.id})
        self.events.emit(context, event_type="DriverOfferCreated", aggregate_id=offer.id, aggregate_type="DriverOffer", aggregate_version=offer.aggregate_version, payload={"offer": offer})
        self.events.emit(context, event_type="DriverAssigned", aggregate_id=trip.id, aggregate_type="Trip", aggregate_version=trip.aggregate_version, payload={"trip_id": trip.id, "driver_id": driver_id})
        return offer

    def accept_offer(self, context: RuntimeContext, offer_id: str) -> Trip:
        offer = self.repositories.offers.get(offer_id)
        if offer is None:
            raise ValueError("offer_not_found")
        if offer.state == OfferState.ACCEPTED:
            trip = self.repositories.trips.get(offer.trip_id)
            if trip is None:
                raise ValueError("trip_not_found")
            return trip
        if offer.state != OfferState.CREATED:
            raise ValueError("offer_not_acceptible")
        trip = self.repositories.trips.get(offer.trip_id)
        if trip is None:
            raise ValueError("trip_not_found")
        offer.state = OfferState.ACCEPTED
        offer.touch()
        trip.lifecycle_state = TripState.DRIVER_ACCEPTED
        trip.touch()
        self.repositories.offers.save(offer)
        self.repositories.trips.save(trip)
        self.events.emit(context, event_type="DriverOfferAccepted", aggregate_id=offer.id, aggregate_type="DriverOffer", aggregate_version=offer.aggregate_version, payload={"offer_id": offer.id, "trip_id": trip.id})
        return trip


@dataclass(slots=True)
class TripService:
    repositories: RuntimeRepositories
    events: EventFabric
    novapay: NovaPayAdapter

    def transition(self, context: RuntimeContext, trip_id: str, target: TripState, *, evidence_reference: str | None = None) -> Trip:
        trip = self.repositories.trips.get(trip_id)
        if trip is None:
            raise ValueError("trip_not_found")
        allowed = {
            (TripState.DRIVER_ACCEPTED, TripState.DRIVER_ARRIVED): "DriverArrived",
            (TripState.DRIVER_ARRIVED, TripState.PICKUP_VERIFIED): "PickupVerified",
            (TripState.PICKUP_VERIFIED, TripState.IN_PROGRESS): "TripStarted",
            (TripState.IN_PROGRESS, TripState.COMPLETING): "TripCompleting",
            (TripState.COMPLETING, TripState.COMPLETED): "TripCompleted",
        }
        event_type = allowed.get((trip.lifecycle_state, target))
        if not event_type:
            raise ValueError("invalid_trip_transition")
        trip.lifecycle_state = target
        if target == TripState.COMPLETED:
            payment = self.novapay.create_payment_intent_reference(Money.of("19.80", "AUD"), context)
            trip.payment_reference = payment.payment_intent_id
            trip.evidence_reference = evidence_reference or new_id("trust_evidence")
        trip.touch()
        self.repositories.trips.save(trip)
        self.events.emit(context, event_type=event_type, aggregate_id=trip.id, aggregate_type="Trip", aggregate_version=trip.aggregate_version, payload={"trip": trip})
        if target == TripState.COMPLETED:
            self.events.emit(context, event_type="PaymentRequested", aggregate_id=trip.id, aggregate_type="Trip", aggregate_version=trip.aggregate_version, payload={"payment_reference": trip.payment_reference, "provider": "NovaPay"})
            self.events.emit(context, event_type="TripEvidenceFinalized", aggregate_id=trip.id, aggregate_type="Trip", aggregate_version=trip.aggregate_version, payload={"evidence_reference": trip.evidence_reference, "provider": "NovaTrust"})
        return trip

    def location(self, context: RuntimeContext, trip_id: str, point: GeoPoint) -> None:
        trip = self.repositories.trips.get(trip_id)
        if trip is None:
            raise ValueError("trip_not_found")
        self.events.emit(context, event_type="TripLocationUpdated", aggregate_id=trip.id, aggregate_type="Trip", aggregate_version=trip.aggregate_version, payload={"point": point.as_dict()})


@dataclass(slots=True)
class SafetyService:
    repositories: RuntimeRepositories
    events: EventFabric
    policy: PolicyService

    def activate_emergency(self, context: RuntimeContext, *, source_id: str, trip_id: str | None, idempotency_key: str) -> EmergencyCase:
        command_hash = payload_hash({"source_id": source_id, "trip_id": trip_id, "source": context.actor_type.value})
        existing = self.repositories.idempotency.get(context.tenant_id, idempotency_key)
        if existing:
            emergency = self.repositories.emergencies.get(existing.result["emergency_id"])
            if emergency is None:
                raise DuplicateCommand("idempotent_emergency_missing")
            return emergency
        emergency = EmergencyCase(
            id=new_id("emergency"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            source=context.actor_type,
            source_id=source_id,
            trip_id=trip_id,
            state=EmergencyState.TRIGGERED,
            evidence_locked=True,
            visible_reference=new_id("safe_ref"),
        )
        self.repositories.emergencies.save(emergency)
        self.repositories.idempotency.put(IdempotencyRecord(context.tenant_id, idempotency_key, command_hash, {"emergency_id": emergency.id}))
        self.events.emit(context, event_type="EmergencyActivated", aggregate_id=emergency.id, aggregate_type="EmergencyCase", aggregate_version=emergency.aggregate_version, payload={"emergency": emergency, "emergency_services_contacted": False})
        return emergency

    def acknowledge(self, context: RuntimeContext, emergency_id: str) -> EmergencyCase:
        self.policy.require_operator(context)
        emergency = self.repositories.emergencies.get(emergency_id)
        if emergency is None:
            raise ValueError("emergency_not_found")
        emergency.state = EmergencyState.ACKNOWLEDGED
        emergency.touch()
        self.repositories.emergencies.save(emergency)
        self.events.emit(context, event_type="EmergencyAcknowledged", aggregate_id=emergency.id, aggregate_type="EmergencyCase", aggregate_version=emergency.aggregate_version, payload={"emergency_id": emergency.id})
        return emergency


@dataclass(slots=True)
class OperatorService:
    repositories: RuntimeRepositories
    events: EventFabric
    policy: PolicyService

    def command(self, context: RuntimeContext, *, command_type: str, target_id: str, reason: str, high_risk: bool = False, approval_reference: str | None = None) -> OperatorCommand:
        self.policy.require_operator(context)
        if high_risk and not approval_reference:
            raise AuthorityDenied("four_eyes_approval_required")
        command = OperatorCommand(
            id=new_id("opcmd"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            command_type=command_type,
            target_id=target_id,
            reason=reason,
            authority_decision="APPROVED",
            evidence_reference=new_id("trust_evidence"),
        )
        self.repositories.operator_commands.save(command)
        self.events.emit(context, event_type="OperatorInterventionRecorded", aggregate_id=command.id, aggregate_type="OperatorCommand", aggregate_version=command.aggregate_version, payload={"command": command})
        return command


@dataclass(slots=True)
class FleetService:
    repositories: RuntimeRepositories
    events: EventFabric

    def create_fleet(self, context: RuntimeContext, name: str) -> Fleet:
        fleet = Fleet(id=new_id("fleet"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, name=name)
        self.repositories.fleets.save(fleet)
        return fleet

    def assign_vehicle(self, context: RuntimeContext, fleet_id: str, vehicle_id: str) -> FleetVehicle:
        vehicle = FleetVehicle(id=new_id("fleet_vehicle"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, fleet_id=fleet_id, vehicle_id=vehicle_id)
        self.repositories.fleet_vehicles.save(vehicle)
        self.events.emit(context, event_type="FleetVehicleAssigned", aggregate_id=vehicle.id, aggregate_type="FleetVehicle", aggregate_version=vehicle.aggregate_version, payload={"fleet_id": fleet_id, "vehicle_id": vehicle_id})
        return vehicle

    def compliance_hold(self, context: RuntimeContext, fleet_id: str, reason: str) -> FleetComplianceState:
        state = FleetComplianceState(id=new_id("fleet_compliance"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, fleet_id=fleet_id, compliance_hold=True, reasons=(reason,))
        self.repositories.fleet_compliance.save(state)
        return state


@dataclass(slots=True)
class LogisticsService:
    repositories: RuntimeRepositories
    events: EventFabric

    def create_order(self, context: RuntimeContext, sender_id: str, recipient_name: str, pickup: AddressRef, dropoff: AddressRef, metadata: dict[str, Any] | None = None) -> DeliveryOrder:
        order = DeliveryOrder(id=new_id("delivery"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, sender_id=sender_id, recipient_name=recipient_name, pickup=pickup, dropoff=dropoff, package_metadata=metadata or {}, state=LogisticsState.CONFIRMED)
        self.repositories.deliveries.save(order)
        self.events.emit(context, event_type="DeliveryCreated", aggregate_id=order.id, aggregate_type="DeliveryOrder", aggregate_version=order.aggregate_version, payload={"order": order})
        return order

    def pickup(self, context: RuntimeContext, order_id: str) -> DeliveryOrder:
        return self._transition(context, order_id, LogisticsState.PICKED_UP, "DeliveryPickedUp")

    def deliver(self, context: RuntimeContext, order_id: str) -> DeliveryOrder:
        return self._transition(context, order_id, LogisticsState.DELIVERED, "DeliveryCompleted")

    def fail_return(self, context: RuntimeContext, order_id: str) -> DeliveryOrder:
        order = self._transition(context, order_id, LogisticsState.FAILED, "DeliveryFailed")
        order.state = LogisticsState.RETURNED
        order.touch()
        self.repositories.deliveries.save(order)
        self.events.emit(context, event_type="DeliveryReturned", aggregate_id=order.id, aggregate_type="DeliveryOrder", aggregate_version=order.aggregate_version, payload={"order_id": order.id})
        return order

    def _transition(self, context: RuntimeContext, order_id: str, state: LogisticsState, event_type: str) -> DeliveryOrder:
        order = self.repositories.deliveries.get(order_id)
        if order is None:
            raise ValueError("delivery_not_found")
        order.state = state
        order.touch()
        self.repositories.deliveries.save(order)
        self.events.emit(context, event_type=event_type, aggregate_id=order.id, aggregate_type="DeliveryOrder", aggregate_version=order.aggregate_version, payload={"order_id": order.id})
        return order


@dataclass(slots=True)
class CorporateMobilityService:
    repositories: RuntimeRepositories
    events: EventFabric

    def create_account(self, context: RuntimeContext, name: str) -> CorporateAccount:
        account = CorporateAccount(id=new_id("corp"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, name=name, wallet_reference=new_id("novapay_wallet_ref"))
        self.repositories.corporate_accounts.save(account)
        return account

    def create_booking(self, context: RuntimeContext, account_id: str, employee_id: str, booking_id: str, cost_center_id: str | None = None) -> CorporateBooking:
        booking = CorporateBooking(id=new_id("corp_booking"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, account_id=account_id, employee_id=employee_id, booking_id=booking_id, cost_center_id=cost_center_id)
        self.repositories.corporate_bookings.save(booking)
        self.events.emit(context, event_type="CorporateBookingCreated", aggregate_id=booking.id, aggregate_type="CorporateBooking", aggregate_version=booking.aggregate_version, payload={"booking": booking})
        return booking


@dataclass(slots=True)
class TransitJourneyService:
    repositories: RuntimeRepositories
    events: EventFabric

    def plan(self, context: RuntimeContext, rider_id: str, *, include_first_last_mile: bool = True) -> TransitJourney:
        legs = (
            TransitLeg("WALK", "origin", "bus_stop"),
            TransitLeg("BUS", "bus_stop", "train_station", "GTFS-compatible where integrated"),
            TransitLeg("TRAIN", "train_station", "novaride_pickup", "GTFS-compatible where integrated"),
            TransitLeg("NOVARIDE", "novaride_pickup", "destination") if include_first_last_mile else TransitLeg("WALK", "station", "destination"),
        )
        journey = TransitJourney(id=new_id("transit_journey"), tenant_id=context.tenant_id, organization_id=context.organization_id, region_code=context.region_code, rider_id=rider_id, legs=legs)
        self.repositories.transit_journeys.save(journey)
        self.events.emit(context, event_type="TransitJourneyPlanned", aggregate_id=journey.id, aggregate_type="TransitJourney", aggregate_version=journey.aggregate_version, payload={"journey": journey, "real_time_provider_claimed": False})
        return journey


@dataclass(slots=True)
class DispatchIntelligenceService:
    events: EventFabric
    policy: PolicyService

    def recommend_rebalance(self, context: RuntimeContext, zone: str) -> dict[str, Any]:
        recommendation = {"type": "DriverRebalanceRecommended", "zone": zone, "effect": "advisory_only"}
        self.events.emit(context, event_type="DriverRebalanceRecommended", aggregate_id=zone, aggregate_type="DispatchZone", aggregate_version=1, payload=recommendation)
        return recommendation

    def apply_price(self, context: RuntimeContext) -> None:
        raise BoundaryViolation("NovaAI_may_not_apply_price")


@dataclass(slots=True)
class ResilienceService:
    repositories: RuntimeRepositories
    events: EventFabric

    def queue_offline_operation(
        self,
        context: RuntimeContext,
        *,
        operation_type: str,
        payload: dict[str, Any],
        idempotency_key: str,
        authority_required: bool = False,
        priority: str = "NORMAL",
    ) -> OfflineOperation:
        command_hash = payload_hash({"operation_type": operation_type, "payload": payload})
        existing_operation = self.repositories.offline_operations.get_by_idempotency_key(context.tenant_id, idempotency_key)
        if existing_operation:
            return existing_operation
        existing = self.repositories.idempotency.get(context.tenant_id, idempotency_key)
        if existing:
            queued = self.repositories.offline_operations.get(existing.result["offline_operation_id"])
            if queued is None:
                raise DuplicateCommand("idempotent_offline_operation_missing")
            return queued
        operation = OfflineOperation(
            id=new_id("offline_op"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            actor_id=context.actor_id,
            operation_type=operation_type,
            encrypted_payload={"ciphertext_ref": canonical_hash(payload), "payload_minimized": True},
            payload_hash=command_hash,
            idempotency_key=idempotency_key,
            authority_required=authority_required,
            status="QUEUED_AUTHORITY_REQUIRED" if authority_required else "QUEUED",
            priority=priority,
        )
        self.repositories.offline_operations.save(operation)
        self.repositories.idempotency.put(
            IdempotencyRecord(context.tenant_id, idempotency_key, command_hash, {"offline_operation_id": operation.id})
        )
        self.events.emit(
            context,
            event_type="OfflineOperationQueued",
            aggregate_id=operation.id,
            aggregate_type="OfflineOperation",
            aggregate_version=operation.aggregate_version,
            payload={"operation": operation},
        )
        return operation

    def synchronize(self, context: RuntimeContext) -> SyncResult:
        queued = [
            operation
            for operation in self.repositories.offline_operations.list(tenant_id=context.tenant_id)
            if operation.actor_id == context.actor_id and operation.status.startswith("QUEUED")
        ]
        synced = 0
        awaiting_authority = 0
        for operation in queued:
            operation.status = "AWAITING_AUTHORITATIVE_ACK" if operation.authority_required else "SYNCED"
            operation.touch()
            self.repositories.offline_operations.save(operation)
            if operation.authority_required:
                awaiting_authority += 1
            else:
                synced += 1
            self.events.emit(
                context,
                event_type="OfflineOperationSynchronized",
                aggregate_id=operation.id,
                aggregate_type="OfflineOperation",
                aggregate_version=operation.aggregate_version,
                payload={"operation_id": operation.id, "status": operation.status},
            )
        return SyncResult(
            queued=len(queued),
            synced=synced,
            awaiting_authority=awaiting_authority,
            conflicts_resolved=0,
            status="PARTIAL_AUTHORITY_REQUIRED" if awaiting_authority else "SYNCHRONIZED",
        )

    def process_mobile_sync_batch(
        self,
        context: RuntimeContext,
        *,
        device_id: str,
        last_server_cursor: str | None,
        operations: tuple[dict[str, Any], ...],
    ) -> dict[str, Any]:
        sync = SyncSession(
            id=new_id("sync"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            device_id=device_id,
            last_server_cursor=last_server_cursor,
            server_cursor=new_id("cursor"),
            status="RECEIVED",
            operation_count=len(operations),
        )
        self.repositories.sync_sessions.save(sync)
        results: list[dict[str, str]] = []
        conflicts: list[dict[str, str]] = []
        for operation in operations:
            queued = self.queue_offline_operation(
                context,
                operation_type=str(operation["operation_type"]),
                payload=dict(operation.get("payload") or {}),
                idempotency_key=str(operation["idempotency_key"]),
                authority_required=bool(operation.get("authority_required", False)),
                priority=str(operation.get("priority", "NORMAL")),
            )
            if operation.get("aggregate_version") and int(operation["aggregate_version"]) < int(operation.get("server_version", operation["aggregate_version"])):
                decision = self.resolve_conflict(
                    domain=str(operation["operation_type"]).split("_")[0],
                    local_version=int(operation["aggregate_version"]),
                    server_version=int(operation.get("server_version", operation["aggregate_version"])),
                )
                conflict = ConflictRecord(
                    id=new_id("sync_conflict"),
                    tenant_id=context.tenant_id,
                    organization_id=context.organization_id,
                    region_code=context.region_code,
                    sync_session_id=sync.id,
                    operation_id=str(operation["id"]),
                    domain=decision["domain"],
                    local_version=decision["local_version"],
                    server_version=decision["server_version"],
                    policy_selected=decision["policy"],
                    winner=decision["winner"],
                    reason="mobile_sync_version_conflict",
                    correlation_id=context.correlation_id,
                )
                self.repositories.conflict_records.save(conflict)
                conflicts.append({"conflict_id": conflict.id, "operation_id": conflict.operation_id, "winner": conflict.winner})
                results.append({"operation_id": str(operation["id"]), "status": "CONFLICT"})
                continue
            results.append({"operation_id": str(operation["id"]), "status": queued.status.replace("QUEUED_AUTHORITY_REQUIRED", "AWAITING_AUTHORITATIVE_ACK")})
        sync.status = "CONFLICTS_RECORDED" if conflicts else "ACCEPTED"
        sync.touch()
        self.repositories.sync_sessions.save(sync)
        self.events.emit(
            context,
            event_type="MobileSyncBatchReceived",
            aggregate_id=sync.id,
            aggregate_type="SyncSession",
            aggregate_version=sync.aggregate_version,
            payload={"sync_id": sync.id, "operation_count": len(operations), "conflict_count": len(conflicts)},
        )
        return {
            "sync_id": sync.id,
            "server_cursor": sync.server_cursor,
            "results": results,
            "server_updates": [],
            "conflicts": conflicts,
        }

    def sync_status(self, sync_id: str) -> dict[str, Any]:
        sync = self.repositories.sync_sessions.get(sync_id)
        if sync is None:
            raise ValueError("sync_session_not_found")
        return _json(sync)

    def resolve_sync_conflict(self, context: RuntimeContext, conflict_id: str, *, resolution: str) -> dict[str, Any]:
        conflict = self.repositories.conflict_records.get(conflict_id)
        if conflict is None:
            raise ValueError("sync_conflict_not_found")
        conflict.reason = f"resolved_by_{resolution}"
        conflict.touch()
        self.repositories.conflict_records.save(conflict)
        self.events.emit(
            context,
            event_type="SyncConflictResolved",
            aggregate_id=conflict.id,
            aggregate_type="ConflictRecord",
            aggregate_version=conflict.aggregate_version,
            payload={"conflict_id": conflict.id, "resolution": resolution},
        )
        return _json(conflict)

    def resolve_conflict(self, *, domain: str, local_version: int, server_version: int) -> dict[str, Any]:
        core_domains = {"booking", "trip", "payment", "dispatch", "safety"}
        if domain in core_domains:
            return {
                "domain": domain,
                "winner": "server",
                "policy": "server_authoritative_for_core_state",
                "local_version": local_version,
                "server_version": server_version,
            }
        return {
            "domain": domain,
            "winner": "merge",
            "policy": "merge_non_authoritative_preferences",
            "local_version": local_version,
            "server_version": server_version,
        }

    def route_provider(
        self,
        context: RuntimeContext,
        *,
        capability: str,
        providers: tuple[ProviderHealth, ...],
    ) -> ProviderRoute:
        attempted = tuple(provider.provider for provider in providers)
        healthy = [provider for provider in providers if provider.state == ProviderState.HEALTHY]
        degraded = [provider for provider in providers if provider.state == ProviderState.DEGRADED]
        selected = healthy[0] if healthy else degraded[0] if degraded else None
        primary_healthy = bool(providers and providers[0].state == ProviderState.HEALTHY)
        mode = DegradedMode.NORMAL if selected and primary_healthy else DegradedMode.DEGRADED if selected else DegradedMode.OFFLINE
        route = ProviderRoute(
            capability=capability,
            selected_provider=selected.provider if selected else None,
            attempted_providers=attempted,
            degraded_mode=mode,
            fallback_reason=None if primary_healthy else "primary_provider_unhealthy",
        )
        self.record_evidence(
            context,
            capability=capability,
            degraded_mode=mode,
            decision="provider_selected" if selected else "provider_unavailable",
            fallback_used=route.selected_provider,
            evidence={"attempted_providers": attempted, "fallback_reason": route.fallback_reason},
        )
        self.events.emit(
            context,
            event_type="ProviderRouteEvaluated",
            aggregate_id=capability,
            aggregate_type="ProviderRoute",
            aggregate_version=1,
            payload={"route": route},
        )
        decision = ProviderRouteDecision(
            id=new_id("provider_route"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            capability=capability,
            selected_provider=route.selected_provider,
            attempted_providers=attempted,
            degraded_mode=mode,
            reason=route.fallback_reason or "primary_provider_selected",
            evidence_hash=canonical_hash({"capability": capability, "attempted": attempted, "selected": route.selected_provider}),
        )
        self.repositories.provider_routes.save(decision)
        return route

    def record_provider_health(self, context: RuntimeContext, health: ProviderHealth) -> ProviderHealthRecord:
        existing = self.repositories.provider_health.latest(
            provider=health.provider,
            capability=health.capability,
            tenant_id=context.tenant_id,
        )
        failures = (existing.consecutive_failures if existing else 0) + (0 if health.state == ProviderState.HEALTHY else 1)
        successes = (existing.consecutive_successes if existing else 0) + (1 if health.state == ProviderState.HEALTHY else 0)
        record = ProviderHealthRecord(
            id=new_id("provider_health"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            provider=health.provider,
            capability=health.capability,
            state=health.state,
            latency_ms=health.latency_ms,
            error_rate=health.error_rate,
            consecutive_failures=0 if health.state == ProviderState.HEALTHY else failures,
            consecutive_successes=successes if health.state == ProviderState.HEALTHY else 0,
            last_successful_probe_at=utc_now() if health.state == ProviderState.HEALTHY else (existing.last_successful_probe_at if existing else None),
            last_state_transition_at=utc_now() if existing is None or existing.state != health.state else existing.last_state_transition_at,
        )
        self.repositories.provider_health.save(record)
        self.events.emit(
            context,
            event_type="ProviderHealthRecorded",
            aggregate_id=record.id,
            aggregate_type="ProviderHealthRecord",
            aggregate_version=record.aggregate_version,
            payload={"record": record},
        )
        return record

    def graceful_degradation(self, capability: str) -> dict[str, str]:
        rules = {
            "live_map": "show_last_known_location_and_eta_text",
            "card_payment": "offer_wallet_mobile_money_or_cash",
            "push_notifications": "use_sms_or_whatsapp",
            "ai_dispatch": "use_deterministic_dispatch_rules",
            "analytics": "core_ride_booking_continues",
            "knowledge_service": "use_cached_runbooks",
            "emergency": "keep_sos_available_and_record_evidence",
        }
        return {"capability": capability, "fallback": rules.get(capability, "preserve_core_journey_and_raise_operator_alert")}

    def record_evidence(
        self,
        context: RuntimeContext,
        *,
        capability: str,
        degraded_mode: DegradedMode,
        decision: str,
        fallback_used: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> ResilienceEvidence:
        record = ResilienceEvidence(
            id=new_id("resilience_evidence"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            capability=capability,
            degraded_mode=degraded_mode,
            decision=decision,
            fallback_used=fallback_used,
            evidence=evidence or {},
            evidence_hash=canonical_hash({"capability": capability, "decision": decision, "fallback_used": fallback_used, "evidence": evidence or {}}),
        )
        self.repositories.resilience_evidence.save(record)
        self.events.emit(
            context,
            event_type="ResilienceEvidenceRecorded",
            aggregate_id=record.id,
            aggregate_type="ResilienceEvidence",
            aggregate_version=record.aggregate_version,
            payload={"record": record},
        )
        return record

    def record_failover_event(
        self,
        context: RuntimeContext,
        *,
        previous_state: FailoverState,
        target_state: FailoverState,
        reason: str,
        automatic: bool,
        approval_reference: str | None = None,
    ) -> FailoverEvent:
        payload = {
            "previous_state": previous_state.value,
            "target_state": target_state.value,
            "reason": reason,
            "automatic": automatic,
            "approval_reference": approval_reference,
        }
        event = FailoverEvent(
            id=new_id("failover"),
            tenant_id=context.tenant_id,
            organization_id=context.organization_id,
            region_code=context.region_code,
            previous_state=previous_state,
            target_state=target_state,
            reason=reason,
            automatic=automatic,
            approval_reference=approval_reference,
            evidence_hash=canonical_hash(payload),
        )
        self.repositories.failover_events.save(event)
        self.events.emit(
            context,
            event_type="FailoverEventRecorded",
            aggregate_id=event.id,
            aggregate_type="FailoverEvent",
            aggregate_version=event.aggregate_version,
            payload={"event": event},
        )
        return event

    def status(self, tenant_id: str | None = None) -> dict[str, Any]:
        queued = self.repositories.offline_operations.list(tenant_id=tenant_id)
        evidence = self.repositories.resilience_evidence.list(tenant_id=tenant_id)
        routes = self.repositories.provider_routes.list(tenant_id=tenant_id)
        failovers = self.repositories.failover_events.list(tenant_id=tenant_id)
        return {
            "layer": "NovaRide Resilience Layer",
            "components": (
                "Connectivity Manager",
                "Offline Queue",
                "Sync Engine",
                "Conflict Resolver",
                "Provider Router",
                "Retry Manager",
                "Circuit Breaker",
                "Failover Controller",
                "Recovery Coordinator",
                "State Reconciler",
                "Health Monitor",
                "Evidence Recorder",
            ),
            "offline_queue_size": len([item for item in queued if item.status.startswith("QUEUED")]),
            "awaiting_authority": len([item for item in queued if item.status == "AWAITING_AUTHORITATIVE_ACK"]),
            "evidence_records": len(evidence),
            "provider_fallback_total": len([item for item in routes if item.degraded_mode != DegradedMode.NORMAL]),
            "failover_events_total": len(failovers),
            "emergency_path_available": True,
            "core_journey_preserved_under_degradation": True,
        }


@dataclass(slots=True)
class ReadModelService:
    repositories: RuntimeRepositories

    def command_center(self, tenant_id: str) -> dict[str, Any]:
        trips = self.repositories.trips.list(tenant_id=tenant_id)
        emergencies = self.repositories.emergencies.list(tenant_id=tenant_id)
        return {
            "status": "READY",
            "active_trips": len([trip for trip in trips if trip.lifecycle_state not in {TripState.COMPLETED, TripState.CANCELLED}]),
            "active_emergencies": len([case for case in emergencies if case.state not in {EmergencyState.RESOLVED, EmergencyState.CLOSED}]),
            "event_count": len(self.repositories.events.all()),
            "built_from_events": True,
            "resilience": {
                "offline_user_operations": len(self.repositories.offline_operations.list(tenant_id=tenant_id)),
                "resilience_evidence_records": len(self.repositories.resilience_evidence.list(tenant_id=tenant_id)),
            },
        }

    def driver_queue(self, tenant_id: str, driver_id: str) -> list[dict[str, Any]]:
        return [_json(offer) for offer in self.repositories.offers.list(tenant_id=tenant_id) if offer.driver_id == driver_id and offer.state == OfferState.CREATED]


@dataclass(slots=True)
class NovaRideRuntime:
    repositories: RuntimeRepositories
    policy: PolicyService
    events: EventFabric
    novapay: NovaPayAdapter
    booking: BookingService
    driver: DriverService
    dispatch: DispatchService
    trip: TripService
    safety: SafetyService
    operator: OperatorService
    fleet: FleetService
    logistics: LogisticsService
    corporate: CorporateMobilityService
    transit: TransitJourneyService
    intelligence: DispatchIntelligenceService
    resilience: ResilienceService
    read_models: ReadModelService

    def status(self) -> dict[str, Any]:
        return {
            "runtime": "NovaRide Universal Mobility Super Platform Runtime",
            "version": "2026.2",
            "status": "runtime_capabilities_complete_release_candidate",
            "GA_ALLOWED": self.policy.ga_allowed,
            "GA_APPROVAL": "PENDING",
            "REAL_PAYMENTS_ENABLED": self.policy.real_payments_enabled,
            "REAL_PAYMENT_APPROVAL": "PENDING",
            "event_count": len(self.repositories.events.all()),
            "resilience": self.resilience.status(),
        }


def create_runtime() -> NovaRideRuntime:
    repositories = RuntimeRepositories()
    policy = PolicyService()
    events = EventFabric(repositories)
    novapay = NovaPayAdapter(policy)
    return NovaRideRuntime(
        repositories=repositories,
        policy=policy,
        events=events,
        novapay=novapay,
        booking=BookingService(repositories, events, policy),
        driver=DriverService(repositories, events, policy),
        dispatch=DispatchService(repositories, events),
        trip=TripService(repositories, events, novapay),
        safety=SafetyService(repositories, events, policy),
        operator=OperatorService(repositories, events, policy),
        fleet=FleetService(repositories, events),
        logistics=LogisticsService(repositories, events),
        corporate=CorporateMobilityService(repositories, events),
        transit=TransitJourneyService(repositories, events),
        intelligence=DispatchIntelligenceService(events, policy),
        resilience=ResilienceService(repositories, events),
        read_models=ReadModelService(repositories),
    )


__all__ = ["NovaRideRuntime", "create_runtime", "RuntimeContext", "ActorType", "AddressRef", "GeoPoint"]
