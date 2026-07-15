from __future__ import annotations

from afritech.novaride_runtime.common.geography import AddressRef, GeoPoint
from afritech.novaride_runtime.models import ActorType, BookingIntent, EmergencyState, RuntimeContext, TripState
from afritech.novaride_runtime.services import create_runtime


def _ctx(actor_type: ActorType = ActorType.RIDER, actor_id: str = "rider_1") -> RuntimeContext:
    return RuntimeContext(
        tenant_id="tenant_test",
        organization_id="org_test",
        region_code="AU",
        actor_type=actor_type,
        actor_id=actor_id,
        correlation_id="corr_e2e",
    )


def test_rider_booking_dispatch_trip_completion_evidence_and_read_model() -> None:
    runtime = create_runtime()
    rider_ctx = _ctx()
    driver_ctx = _ctx(ActorType.DRIVER, "driver_1")
    system_ctx = _ctx(ActorType.SYSTEM, "system")

    runtime.driver.onboard(driver_ctx, identity_id="novaid_driver_1", display_name="Driver One", vehicle_id="vehicle_1")
    runtime.driver.start_shift(driver_ctx, "driver_1")
    availability = runtime.driver.set_available(driver_ctx, "driver_1")
    assert availability.dispatchable is True

    quote = runtime.booking.create_quote(rider_ctx, service_type="economy", currency="AUD")
    booking = runtime.booking.create_booking(
        rider_ctx,
        BookingIntent("rider_1", AddressRef("A", GeoPoint(-37.81, 144.96)), AddressRef("B", GeoPoint(-37.82, 144.97)), "economy"),
        quote_id=quote.id,
        idempotency_key="book-1",
    )
    assert runtime.booking.create_booking(
        rider_ctx,
        BookingIntent("rider_1", AddressRef("A"), AddressRef("B"), "economy"),
        quote_id=quote.id,
        idempotency_key="book-1",
    ).id == booking.id

    offer = runtime.dispatch.start_dispatch(system_ctx, booking.id)
    trip = runtime.dispatch.accept_offer(driver_ctx, offer.id)
    assert trip.lifecycle_state == TripState.DRIVER_ACCEPTED

    runtime.trip.transition(driver_ctx, trip.id, TripState.DRIVER_ARRIVED)
    runtime.trip.transition(driver_ctx, trip.id, TripState.PICKUP_VERIFIED)
    runtime.trip.transition(driver_ctx, trip.id, TripState.IN_PROGRESS)
    runtime.trip.location(driver_ctx, trip.id, GeoPoint(-37.82, 144.97))
    runtime.trip.transition(driver_ctx, trip.id, TripState.COMPLETING)
    completed = runtime.trip.transition(driver_ctx, trip.id, TripState.COMPLETED)

    assert completed.payment_reference.startswith("payintent_sandbox")
    assert completed.evidence_reference.startswith("trust_evidence")
    assert "TripEvidenceFinalized" in {event.event_type for event in runtime.repositories.events.all()}
    assert runtime.read_models.command_center("tenant_test")["built_from_events"] is True
    assert runtime.repositories.events.by_correlation("corr_e2e")


def test_safety_operator_fleet_logistics_corporate_transit_and_payment_boundaries() -> None:
    runtime = create_runtime()
    rider_ctx = _ctx()
    operator_ctx = _ctx(ActorType.OPERATOR, "operator_1")
    driver_ctx = _ctx(ActorType.DRIVER, "driver_1")

    emergency = runtime.safety.activate_emergency(rider_ctx, source_id="rider_1", trip_id=None, idempotency_key="em-1")
    assert emergency.evidence_locked is True
    assert runtime.safety.activate_emergency(rider_ctx, source_id="rider_1", trip_id=None, idempotency_key="em-1").id == emergency.id
    acknowledged = runtime.safety.acknowledge(operator_ctx, emergency.id)
    assert acknowledged.state == EmergencyState.ACKNOWLEDGED

    fleet = runtime.fleet.create_fleet(operator_ctx, "Pilot Fleet")
    vehicle = runtime.fleet.assign_vehicle(operator_ctx, fleet.id, "vehicle_1")
    assert vehicle.fleet_id == fleet.id
    assert runtime.fleet.compliance_hold(operator_ctx, fleet.id, "inspection_expired").compliance_hold is True

    delivery = runtime.logistics.create_order(rider_ctx, "rider_1", "Recipient", AddressRef("Pickup"), AddressRef("Dropoff"))
    runtime.logistics.pickup(driver_ctx, delivery.id)
    delivered = runtime.logistics.deliver(driver_ctx, delivery.id)
    assert delivered.state == "DELIVERED"

    account = runtime.corporate.create_account(operator_ctx, "Acme")
    corporate_booking = runtime.corporate.create_booking(operator_ctx, account.id, "employee_1", "booking_ref", "CC-1")
    assert corporate_booking.cost_center_id == "CC-1"

    journey = runtime.transit.plan(rider_ctx, "rider_1")
    assert [leg.mode for leg in journey.legs] == ["WALK", "BUS", "TRAIN", "NOVARIDE"]

    payment = runtime.novapay.create_payment_intent_reference(__import__("afritech.novaride_runtime.common.money", fromlist=["Money"]).Money.of("10", "AUD"), rider_ctx)
    assert payment.provider == "NovaPay"
    assert payment.real_payment_enabled is False
    assert runtime.status()["GA_ALLOWED"] is False
    assert runtime.status()["REAL_PAYMENTS_ENABLED"] is False
