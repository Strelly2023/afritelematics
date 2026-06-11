"""Canonical data ownership registry for decentralized AfriTech domains."""

from __future__ import annotations

from afritech.data_governance.contracts import (
    DataGovernanceViolation,
    DomainDataContract,
)


DATA_OWNERSHIP_REGISTRY: tuple[DomainDataContract, ...] = (
    DomainDataContract(
        domain="AfriRide",
        owned_resources=("rides", "driver_availability", "ride_events"),
    ),
    DomainDataContract(
        domain="AfriConnectTL",
        owned_resources=("shipments", "delivery_receipts", "logistics_events"),
    ),
    DomainDataContract(
        domain="AfriEats",
        owned_resources=("food_orders", "restaurant_acceptance", "meal_delivery_events"),
    ),
    DomainDataContract(
        domain="AfriPay",
        owned_resources=("raw_transaction_evidence",),
        write_authority=False,
    ),
    DomainDataContract(
        domain="AfriID",
        owned_resources=("actors", "device_keys", "credentials"),
    ),
)


def owner_for_resource(resource: str) -> str:
    for contract in DATA_OWNERSHIP_REGISTRY:
        if resource in contract.owned_resources:
            return contract.domain
    raise DataGovernanceViolation(f"unknown data resource: {resource}")


def resources_for_domain(domain: str) -> tuple[str, ...]:
    for contract in DATA_OWNERSHIP_REGISTRY:
        if contract.domain == domain:
            return contract.owned_resources
    raise DataGovernanceViolation(f"unknown data domain: {domain}")
