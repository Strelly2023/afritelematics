from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import json

import pytest

from afritech.novalogistics import (
    Address,
    Claim,
    ClaimStatus,
    Contact,
    Customer,
    Delivery,
    DeliveryStatus,
    DomainError,
    GeoCoordinate,
    Identifier,
    InvalidTransition,
    Order,
    OrderStatus,
    Quote,
    QuoteStatus,
    Shipment,
    ShipmentStatus,
)


NOW = datetime(2026, 8, 6, tzinfo=timezone.utc)


def test_value_objects_normalize_validate_and_compare():
    assert Identifier("  shipment-1 ") == Identifier("shipment-1")
    assert Address(" 1 Main  St ", " Melbourne ", "au").country_code == "AU"
    assert Contact(" Alex  Smith ", email=" A@EXAMPLE.COM ").email == "a@example.com"
    assert GeoCoordinate(-37.8, 144.9) == GeoCoordinate(-37.8, 144.9)
    with pytest.raises(DomainError):
        GeoCoordinate(91, 0)
    with pytest.raises(DomainError):
        Contact("Alex")


def test_records_are_immutable_and_tenant_scoped():
    customer = Customer(Identifier("c-1"), Identifier("tenant-1"), " ACME  Ltd ")
    assert customer.name == "ACME Ltd"
    with pytest.raises(FrozenInstanceError):
        customer.name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("aggregate", "target"),
    [
        (Quote(Identifier("q"), Identifier("t"), QuoteStatus.DRAFT), QuoteStatus.OFFERED),
        (Order(Identifier("o"), Identifier("t"), OrderStatus.DRAFT), OrderStatus.CONFIRMED),
        (Shipment(Identifier("s"), Identifier("t"), ShipmentStatus.DRAFT), ShipmentStatus.BOOKED),
        (Delivery(Identifier("d"), Identifier("t"), DeliveryStatus.SCHEDULED), DeliveryStatus.OUT_FOR_DELIVERY),
        (Claim(Identifier("c"), Identifier("t"), ClaimStatus.OPEN), ClaimStatus.UNDER_REVIEW),
    ],
)
def test_legal_transitions_emit_tenant_scoped_events(aggregate, target):
    changed = aggregate.transition(target, at=NOW)
    assert changed.version == 1
    assert changed.events[-1].tenant_id == aggregate.tenant_id
    assert changed.events[-1].occurred_at == NOW


def test_illegal_transition_is_rejected_and_replay_is_idempotent():
    shipment = Shipment(Identifier("s"), Identifier("t"), ShipmentStatus.DRAFT)
    with pytest.raises(InvalidTransition):
        shipment.transition(ShipmentStatus.DELIVERED, at=NOW)
    assert shipment.transition(ShipmentStatus.DRAFT, at=NOW) is shipment


def test_serialization_deserialization_preserves_equality_and_events():
    original = Shipment(Identifier("s"), Identifier("tenant"), ShipmentStatus.DRAFT)
    original = original.transition(ShipmentStatus.BOOKED, at=NOW, reason="confirmed")
    payload = json.loads(json.dumps(original.to_dict()))
    restored = Shipment.from_dict(payload)
    assert restored == original
    assert restored.events[0].data["reason"] == "confirmed"


def test_naive_event_timestamp_is_rejected():
    shipment = Shipment(Identifier("s"), Identifier("t"), ShipmentStatus.DRAFT)
    with pytest.raises(DomainError):
        shipment.transition(ShipmentStatus.BOOKED, at=datetime(2026, 1, 1))


def test_compatibility_imports_remain_available():
    from afritech.mobility.logistics_custody_chain import CustodyChain
    from afritech.novaride_runtime import logistics

    assert CustodyChain is not None
    assert logistics is not None
