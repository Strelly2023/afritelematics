from dataclasses import FrozenInstanceError

import pytest

from afritech.novapay import (
    AuthorityKind,
    CapabilityAuthority,
    CapabilityStatus,
    CAPABILITY_AUTHORITIES,
    NOVAPAY_PRODUCT_OWNER,
    PROHIBITED_DUPLICATION,
    authority_for,
    financial_source_of_truth,
    validate_authority_map,
)


def test_authority_map_is_valid() -> None:
    assert validate_authority_map() == ()


def test_double_entry_ledger_is_the_single_financial_source_of_truth() -> None:
    source = financial_source_of_truth()

    assert source.capability == "double_entry_ledger"
    assert source.authority_kind is AuthorityKind.FINANCIAL
    assert source.canonical_owner == NOVAPAY_PRODUCT_OWNER
    assert source.source_of_truth is True
    assert source.may_mutate_financial_state is True


def test_wallet_balance_is_a_projection_only() -> None:
    wallet_balance = authority_for("wallet_balance")

    assert wallet_balance.status is CapabilityStatus.PROJECTION_ONLY
    assert wallet_balance.source_of_truth is False
    assert wallet_balance.may_mutate_financial_state is False


def test_provider_execution_is_never_ledger_truth() -> None:
    provider = authority_for("provider_execution")

    assert provider.status is CapabilityStatus.ADAPTER_ONLY
    assert provider.source_of_truth is False
    assert provider.may_mutate_financial_state is False
    assert "never define authoritative ledger balances" in provider.notes


def test_novaride_is_a_consumer_not_payment_authority() -> None:
    integration = authority_for("novaride_payment_integration")

    assert integration.canonical_owner == "NovaRide"
    assert integration.status is CapabilityStatus.CONSUMER_ONLY
    assert integration.source_of_truth is False
    assert integration.may_mutate_financial_state is False


def test_existing_afripay_wallet_and_ledger_are_recorded_as_legacy_compatible() -> None:
    wallet = authority_for("wallet_service")
    ledger = authority_for("double_entry_ledger")

    assert wallet.current_implementation == "afritech.afripay.wallet"
    assert ledger.current_implementation == "afritech.afripay.ledger"
    assert wallet.status is CapabilityStatus.LEGACY_COMPATIBLE
    assert ledger.status is CapabilityStatus.LEGACY_COMPATIBLE


def test_authority_entries_are_immutable() -> None:
    entry = authority_for("double_entry_ledger")

    with pytest.raises(FrozenInstanceError):
        entry.capability = "other"  # type: ignore[misc]


def test_authority_mapping_is_immutable() -> None:
    with pytest.raises(TypeError):
        CAPABILITY_AUTHORITIES["other"] = authority_for(  # type: ignore[index]
            "double_entry_ledger"
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "capability",
        "canonical_owner",
        "current_implementation",
        "notes",
    ),
)
def test_authority_requires_non_empty_text(field_name: str) -> None:
    values = {
        "capability": "example",
        "authority_kind": AuthorityKind.IMPLEMENTATION,
        "canonical_owner": NOVAPAY_PRODUCT_OWNER,
        "current_implementation": "example.module",
        "status": CapabilityStatus.CANONICAL,
        "source_of_truth": False,
        "may_mutate_financial_state": False,
        "notes": "Example declaration",
    }
    values[field_name] = "   "

    with pytest.raises(ValueError, match=field_name):
        CapabilityAuthority(**values)


def test_non_authoritative_capability_cannot_mutate_financial_state() -> None:
    with pytest.raises(
        ValueError,
        match="may mutate financial state only",
    ):
        CapabilityAuthority(
            capability="invalid",
            authority_kind=AuthorityKind.ADAPTER,
            canonical_owner=NOVAPAY_PRODUCT_OWNER,
            current_implementation="example.adapter",
            status=CapabilityStatus.ADAPTER_ONLY,
            source_of_truth=False,
            may_mutate_financial_state=True,
            notes="Invalid authority",
        )


@pytest.mark.parametrize(
    "status",
    (
        CapabilityStatus.PROJECTION_ONLY,
        CapabilityStatus.ADAPTER_ONLY,
        CapabilityStatus.CONSUMER_ONLY,
    ),
)
def test_projection_adapter_and_consumer_cannot_be_source_of_truth(
    status: CapabilityStatus,
) -> None:
    with pytest.raises(ValueError, match="cannot be sources of truth"):
        CapabilityAuthority(
            capability="invalid",
            authority_kind=AuthorityKind.PROJECTION,
            canonical_owner=NOVAPAY_PRODUCT_OWNER,
            current_implementation="example.module",
            status=status,
            source_of_truth=True,
            may_mutate_financial_state=False,
            notes="Invalid authority",
        )


def test_unknown_capability_fails_closed() -> None:
    with pytest.raises(KeyError, match="unknown NovaPay capability"):
        authority_for("unknown")


def test_empty_capability_fails_closed() -> None:
    with pytest.raises(ValueError, match="capability must be provided"):
        authority_for("   ")


def test_prohibited_duplication_contains_required_boundaries() -> None:
    combined = " ".join(PROHIBITED_DUPLICATION).lower()

    assert "client-side balance mutation" in combined
    assert "provider callbacks treated as ledger truth" in combined
    assert "novaride-owned authoritative payment ledger" in combined
