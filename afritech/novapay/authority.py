"""Canonical NovaPay wallet and ledger authority declarations.

This module defines architectural ownership and financial-authority boundaries.
It intentionally contains no balance mutation, posting, settlement, or provider
execution logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class AuthorityKind(str, Enum):
    """Kinds of authority recognised by NovaPay."""

    PRODUCT = "product"
    FINANCIAL = "financial"
    IMPLEMENTATION = "implementation"
    PROJECTION = "projection"
    ADAPTER = "adapter"
    CONSUMER = "consumer"


class CapabilityStatus(str, Enum):
    """Migration status for a NovaPay capability."""

    CANONICAL = "canonical"
    LEGACY_COMPATIBLE = "legacy_compatible"
    PROJECTION_ONLY = "projection_only"
    ADAPTER_ONLY = "adapter_only"
    CONSUMER_ONLY = "consumer_only"


@dataclass(frozen=True, slots=True)
class CapabilityAuthority:
    """Immutable authority declaration for a single capability."""

    capability: str
    authority_kind: AuthorityKind
    canonical_owner: str
    current_implementation: str
    status: CapabilityStatus
    source_of_truth: bool
    may_mutate_financial_state: bool
    notes: str

    def __post_init__(self) -> None:
        for field_name in (
            "capability",
            "canonical_owner",
            "current_implementation",
            "notes",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")

        object.__setattr__(self, "capability", self.capability.strip())
        object.__setattr__(self, "canonical_owner", self.canonical_owner.strip())
        object.__setattr__(
            self,
            "current_implementation",
            self.current_implementation.strip(),
        )
        object.__setattr__(self, "notes", self.notes.strip())

        if self.source_of_truth and self.status in {
            CapabilityStatus.PROJECTION_ONLY,
            CapabilityStatus.ADAPTER_ONLY,
            CapabilityStatus.CONSUMER_ONLY,
        }:
            raise ValueError(
                "projection, adapter, and consumer capabilities "
                "cannot be sources of truth"
            )

        if self.may_mutate_financial_state and not self.source_of_truth:
            raise ValueError(
                "a capability may mutate financial state only when it is "
                "declared as a source of truth"
            )


NOVAPAY_PRODUCT_OWNER = "NovaPay"
LEGACY_PAYMENT_ENGINE = "afritech.afripay"
CANONICAL_NOVAPAY_PACKAGE = "afritech.novapay"


_AUTHORITY_ENTRIES = (
    CapabilityAuthority(
        capability="product_contract",
        authority_kind=AuthorityKind.PRODUCT,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation=CANONICAL_NOVAPAY_PACKAGE,
        status=CapabilityStatus.CANONICAL,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "NovaPay owns customer-facing payment contracts, product policy, "
            "API semantics, and downstream integration boundaries."
        ),
    ),
    CapabilityAuthority(
        capability="double_entry_ledger",
        authority_kind=AuthorityKind.FINANCIAL,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="afritech.afripay.ledger",
        status=CapabilityStatus.LEGACY_COMPATIBLE,
        source_of_truth=True,
        may_mutate_financial_state=True,
        notes=(
            "Balanced journal entries are the authoritative financial record. "
            "The existing AfriPay ledger remains operational during migration."
        ),
    ),
    CapabilityAuthority(
        capability="wallet_service",
        authority_kind=AuthorityKind.IMPLEMENTATION,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="afritech.afripay.wallet",
        status=CapabilityStatus.LEGACY_COMPATIBLE,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "Wallet commands must ultimately be represented by authoritative "
            "ledger postings. Wallet balances must not become an independent "
            "financial authority."
        ),
    ),
    CapabilityAuthority(
        capability="wallet_balance",
        authority_kind=AuthorityKind.PROJECTION,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="NovaPay wallet read models",
        status=CapabilityStatus.PROJECTION_ONLY,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "Displayed wallet balances are ledger-derived projections and "
            "must never be invented or independently mutated by clients."
        ),
    ),
    CapabilityAuthority(
        capability="payment_orchestration",
        authority_kind=AuthorityKind.IMPLEMENTATION,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="afritech.afripay.orchestration",
        status=CapabilityStatus.LEGACY_COMPATIBLE,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "Payment orchestration coordinates validated commands, ledger "
            "posting, provider execution, receipts, and lifecycle events."
        ),
    ),
    CapabilityAuthority(
        capability="reconciliation",
        authority_kind=AuthorityKind.IMPLEMENTATION,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="afritech.afripay.reconciliation",
        status=CapabilityStatus.LEGACY_COMPATIBLE,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "Reconciliation compares provider, treasury, transaction, event, "
            "and ledger evidence without allowing providers to redefine truth."
        ),
    ),
    CapabilityAuthority(
        capability="treasury",
        authority_kind=AuthorityKind.IMPLEMENTATION,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="afritech.afripay.treasury",
        status=CapabilityStatus.LEGACY_COMPATIBLE,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "Treasury manages liquidity and reservations subject to ledger, "
            "settlement, policy, and reconciliation controls."
        ),
    ),
    CapabilityAuthority(
        capability="provider_execution",
        authority_kind=AuthorityKind.ADAPTER,
        canonical_owner=NOVAPAY_PRODUCT_OWNER,
        current_implementation="NovaPay and AfriPay provider adapters",
        status=CapabilityStatus.ADAPTER_ONLY,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "Provider responses and callbacks are external execution evidence; "
            "they never define authoritative ledger balances."
        ),
    ),
    CapabilityAuthority(
        capability="novaride_payment_integration",
        authority_kind=AuthorityKind.CONSUMER,
        canonical_owner="NovaRide",
        current_implementation="NovaRide NovaPay integration adapters",
        status=CapabilityStatus.CONSUMER_ONLY,
        source_of_truth=False,
        may_mutate_financial_state=False,
        notes=(
            "NovaRide requests payment operations through NovaPay contracts "
            "and must not maintain an independent authoritative payment ledger."
        ),
    ),
)


CAPABILITY_AUTHORITIES: Mapping[str, CapabilityAuthority] = MappingProxyType(
    {entry.capability: entry for entry in _AUTHORITY_ENTRIES}
)


PROHIBITED_DUPLICATION = (
    "Independent authoritative wallet balances outside the NovaPay ledger",
    "Provider callbacks treated as ledger truth",
    "Client-side balance mutation",
    "NovaRide-owned authoritative payment ledger",
    "Separate unbalanced posting engines",
    "Silent migration that changes existing financial behaviour",
)


def authority_for(capability: str) -> CapabilityAuthority:
    """Return the authority declaration for a capability."""

    normalized = str(capability).strip().lower()
    if not normalized:
        raise ValueError("capability must be provided")

    try:
        return CAPABILITY_AUTHORITIES[normalized]
    except KeyError as exc:
        raise KeyError(f"unknown NovaPay capability: {normalized}") from exc


def financial_source_of_truth() -> CapabilityAuthority:
    """Return the one declared authoritative financial capability."""

    entries = tuple(
        entry for entry in CAPABILITY_AUTHORITIES.values() if entry.source_of_truth
    )
    if len(entries) != 1:
        raise RuntimeError(
            "NovaPay must declare exactly one financial source of truth"
        )
    return entries[0]


def validate_authority_map() -> tuple[str, ...]:
    """Return validation errors for the complete authority map."""

    errors: list[str] = []

    if len(CAPABILITY_AUTHORITIES) != len(_AUTHORITY_ENTRIES):
        errors.append("capability names must be unique")

    source_entries = tuple(
        entry for entry in CAPABILITY_AUTHORITIES.values() if entry.source_of_truth
    )

    if len(source_entries) != 1:
        errors.append("exactly one financial source of truth must be declared")
    elif source_entries[0].capability != "double_entry_ledger":
        errors.append("double_entry_ledger must be the financial source of truth")

    for name, entry in CAPABILITY_AUTHORITIES.items():
        if name != entry.capability:
            errors.append(f"authority key mismatch for {name}")

        if entry.canonical_owner == NOVAPAY_PRODUCT_OWNER:
            continue

        if entry.status is not CapabilityStatus.CONSUMER_ONLY:
            errors.append(
                f"non-consumer capability {name} must be owned by NovaPay"
            )

    return tuple(errors)


__all__ = [
    "AuthorityKind",
    "CapabilityAuthority",
    "CapabilityStatus",
    "CANONICAL_NOVAPAY_PACKAGE",
    "CAPABILITY_AUTHORITIES",
    "LEGACY_PAYMENT_ENGINE",
    "NOVAPAY_PRODUCT_OWNER",
    "PROHIBITED_DUPLICATION",
    "authority_for",
    "financial_source_of_truth",
    "validate_authority_map",
]
