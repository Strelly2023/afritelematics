from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from types import MappingProxyType

import pytest

from afritech.novapay.domain import transfer
from afritech.novapay.domain.transfer import (
    TransferAccountReference,
    TransferDirection,
    TransferId,
    TransferMetadata,
    TransferPartyReference,
    TransferPriority,
    TransferPurpose,
    TransferReference,
    TransferStatus,
    TransferType,
)


def test_transfer_id_normalizes_whitespace() -> None:
    value = TransferId(" transfer-001 ")

    assert value.value == "transfer-001"
    assert value.canonical() == "transfer-001"
    assert str(value) == "transfer-001"


def test_transfer_id_of_preserves_existing_instance() -> None:
    original = TransferId("transfer-001")

    assert TransferId.of(original) is original


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_transfer_id_rejects_blank_value(
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="transfer id is required",
    ):
        TransferId(value)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        object(),
    ],
)
def test_transfer_id_rejects_non_string(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="transfer id must be a string",
    ):
        TransferId.of(value)


def test_transfer_id_rejects_excessive_length() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        TransferId("x" * 129)


def test_transfer_id_is_immutable() -> None:
    value = TransferId("transfer-001")

    with pytest.raises(FrozenInstanceError):
        value.value = "changed"  # type: ignore[misc]


def test_transfer_id_uses_slots() -> None:
    assert not hasattr(
        TransferId("transfer-001"),
        "__dict__",
    )


def test_transfer_reference_normalizes_whitespace() -> None:
    value = TransferReference(" client-reference ")

    assert value.value == "client-reference"
    assert value.canonical() == "client-reference"
    assert str(value) == "client-reference"


def test_transfer_reference_of_preserves_instance() -> None:
    original = TransferReference("reference-001")

    assert TransferReference.of(original) is original


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        None,
        42,
    ],
)
def test_transfer_reference_rejects_invalid_value(
    value: object,
) -> None:
    expected = TypeError if not isinstance(value, str) else ValueError

    with pytest.raises(expected):
        TransferReference.of(value)


def test_transfer_reference_rejects_excessive_length() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed",
    ):
        TransferReference("x" * 257)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("draft", TransferStatus.DRAFT),
        (" VALIDATED ", TransferStatus.VALIDATED),
        ("authorized", TransferStatus.AUTHORIZED),
        ("submitted", TransferStatus.SUBMITTED),
        ("processing", TransferStatus.PROCESSING),
        ("completed", TransferStatus.COMPLETED),
        ("failed", TransferStatus.FAILED),
        ("cancelled", TransferStatus.CANCELLED),
        ("reversed", TransferStatus.REVERSED),
        ("expired", TransferStatus.EXPIRED),
    ],
)
def test_transfer_status_parse(
    raw: str,
    expected: TransferStatus,
) -> None:
    assert TransferStatus.parse(raw) is expected


def test_transfer_status_inventory() -> None:
    assert tuple(
        item.value
        for item in TransferStatus
    ) == (
        "draft",
        "validated",
        "authorized",
        "submitted",
        "processing",
        "completed",
        "failed",
        "cancelled",
        "reversed",
        "expired",
    )


@pytest.mark.parametrize(
    "value",
    [
        "unknown",
        "",
        None,
        1,
    ],
)
def test_transfer_status_rejects_invalid_value(
    value: object,
) -> None:
    expected = TypeError if not isinstance(value, str) else ValueError

    with pytest.raises(expected):
        TransferStatus.parse(value)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("internal", TransferType.INTERNAL),
        ("domestic", TransferType.DOMESTIC),
        ("international", TransferType.INTERNATIONAL),
        ("remittance", TransferType.REMITTANCE),
        ("business-payment", TransferType.BUSINESS_PAYMENT),
        ("merchant payment", TransferType.MERCHANT_PAYMENT),
        ("payout", TransferType.PAYOUT),
        ("refund", TransferType.REFUND),
        ("reversal", TransferType.REVERSAL),
    ],
)
def test_transfer_type_parse(
    raw: str,
    expected: TransferType,
) -> None:
    assert TransferType.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("outbound", TransferDirection.OUTBOUND),
        (" INBOUND ", TransferDirection.INBOUND),
        ("internal", TransferDirection.INTERNAL),
    ],
)
def test_transfer_direction_parse(
    raw: str,
    expected: TransferDirection,
) -> None:
    assert TransferDirection.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("general", TransferPurpose.GENERAL),
        ("family support", TransferPurpose.FAMILY_SUPPORT),
        ("education", TransferPurpose.EDUCATION),
        ("medical", TransferPurpose.MEDICAL),
        ("goods-and-services", TransferPurpose.GOODS_AND_SERVICES),
        ("salary", TransferPurpose.SALARY),
        ("business", TransferPurpose.BUSINESS),
        ("savings", TransferPurpose.SAVINGS),
        ("emergency", TransferPurpose.EMERGENCY),
        ("charity", TransferPurpose.CHARITY),
        ("government", TransferPurpose.GOVERNMENT),
        ("refund", TransferPurpose.REFUND),
    ],
)
def test_transfer_purpose_parse(
    raw: str,
    expected: TransferPurpose,
) -> None:
    assert TransferPurpose.parse(raw) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("low", TransferPriority.LOW),
        ("normal", TransferPriority.NORMAL),
        (" HIGH ", TransferPriority.HIGH),
        ("urgent", TransferPriority.URGENT),
    ],
)
def test_transfer_priority_parse(
    raw: str,
    expected: TransferPriority,
) -> None:
    assert TransferPriority.parse(raw) is expected


@pytest.mark.parametrize(
    "enum_type",
    [
        TransferType,
        TransferDirection,
        TransferPurpose,
        TransferPriority,
    ],
)
def test_transfer_enums_reject_unknown_value(
    enum_type: type[object],
) -> None:
    with pytest.raises(ValueError):
        enum_type.parse("unsupported")  # type: ignore[attr-defined]


def test_party_reference_normalizes_values() -> None:
    value = TransferPartyReference(
        party_id=" customer-001 ",
        party_type=" Beneficiary Party ",
        display_name=" Beneficiary Name ",
    )

    assert value.party_id == "customer-001"
    assert value.party_type == "beneficiary_party"
    assert value.display_name == "Beneficiary Name"


def test_party_reference_from_scalar() -> None:
    value = TransferPartyReference.of(
        "customer-001",
        party_type="customer",
        display_name="Customer Name",
    )

    assert value == TransferPartyReference(
        party_id="customer-001",
        party_type="customer",
        display_name="Customer Name",
    )


def test_party_reference_from_mapping() -> None:
    value = TransferPartyReference.of(
        {
            "party_id": "customer-001",
            "party_type": "beneficiary",
            "display_name": "Customer Name",
        }
    )

    assert value.party_id == "customer-001"
    assert value.party_type == "beneficiary"
    assert value.display_name == "Customer Name"


def test_party_reference_preserves_instance() -> None:
    original = TransferPartyReference(
        party_id="customer-001",
        party_type="customer",
    )

    assert TransferPartyReference.of(original) is original


def test_party_reference_rejects_extra_fields_with_instance() -> None:
    original = TransferPartyReference(
        party_id="customer-001",
        party_type="customer",
    )

    with pytest.raises(
        ValueError,
        match="must not be provided",
    ):
        TransferPartyReference.of(
            original,
            party_type="beneficiary",
        )


def test_party_reference_requires_party_type() -> None:
    with pytest.raises(
        ValueError,
        match="party type is required",
    ):
        TransferPartyReference.of("customer-001")


@pytest.mark.parametrize(
    ("party_id", "party_type"),
    [
        ("", "customer"),
        ("customer-001", ""),
        (None, "customer"),
        ("customer-001", None),
    ],
)
def test_party_reference_rejects_invalid_required_fields(
    party_id: object,
    party_type: object,
) -> None:
    expected = (
        TypeError
        if not isinstance(party_id, str)
        or not isinstance(party_type, str)
        else ValueError
    )

    with pytest.raises(expected):
        TransferPartyReference(
            party_id=party_id,  # type: ignore[arg-type]
            party_type=party_type,  # type: ignore[arg-type]
        )


def test_party_reference_canonical_dict() -> None:
    value = TransferPartyReference(
        party_id="customer-001",
        party_type="beneficiary",
        display_name="Customer Name",
    )

    assert value.canonical_dict() == {
        "party_id": "customer-001",
        "party_type": "beneficiary",
        "display_name": "Customer Name",
    }


def test_party_reference_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(TransferPartyReference)
    } == {
        "party_id",
        "party_type",
        "display_name",
    }


def test_account_reference_normalizes_values() -> None:
    value = TransferAccountReference(
        account_id=" wallet-001 ",
        account_type=" Digital Wallet ",
        currency_code="aud",
        institution_reference=" NovaPay AU ",
    )

    assert value.account_id == "wallet-001"
    assert value.account_type == "digital_wallet"
    assert value.currency_code == "AUD"
    assert value.institution_reference == "NovaPay AU"


def test_account_reference_from_scalar() -> None:
    value = TransferAccountReference.of(
        "wallet-001",
        account_type="wallet",
        currency_code="aud",
        institution_reference="novapay-au",
    )

    assert value == TransferAccountReference(
        account_id="wallet-001",
        account_type="wallet",
        currency_code="AUD",
        institution_reference="novapay-au",
    )


def test_account_reference_from_mapping() -> None:
    value = TransferAccountReference.of(
        {
            "account_id": "wallet-001",
            "account_type": "wallet",
            "currency_code": "usd",
            "institution_reference": "novapay-us",
        }
    )

    assert value.account_id == "wallet-001"
    assert value.account_type == "wallet"
    assert value.currency_code == "USD"
    assert value.institution_reference == "novapay-us"


def test_account_reference_preserves_instance() -> None:
    original = TransferAccountReference(
        account_id="wallet-001",
        account_type="wallet",
    )

    assert TransferAccountReference.of(original) is original


def test_account_reference_rejects_extra_fields_with_instance() -> None:
    original = TransferAccountReference(
        account_id="wallet-001",
        account_type="wallet",
    )

    with pytest.raises(
        ValueError,
        match="must not be provided",
    ):
        TransferAccountReference.of(
            original,
            currency_code="AUD",
        )


def test_account_reference_requires_account_type() -> None:
    with pytest.raises(
        ValueError,
        match="account type is required",
    ):
        TransferAccountReference.of("wallet-001")


@pytest.mark.parametrize(
    "currency_code",
    [
        "",
        "A",
        "AU",
        "AUDD",
        "12A",
        "A$D",
    ],
)
def test_account_reference_rejects_invalid_currency_code(
    currency_code: str,
) -> None:
    with pytest.raises(ValueError):
        TransferAccountReference(
            account_id="wallet-001",
            account_type="wallet",
            currency_code=currency_code,
        )


def test_account_reference_allows_missing_currency() -> None:
    value = TransferAccountReference(
        account_id="wallet-001",
        account_type="wallet",
    )

    assert value.currency_code is None


def test_account_reference_canonical_dict() -> None:
    value = TransferAccountReference(
        account_id="wallet-001",
        account_type="wallet",
        currency_code="AUD",
        institution_reference="novapay-au",
    )

    assert value.canonical_dict() == {
        "account_id": "wallet-001",
        "account_type": "wallet",
        "currency_code": "AUD",
        "institution_reference": "novapay-au",
    }


def test_account_reference_exact_field_contract() -> None:
    assert {
        item.name
        for item in fields(TransferAccountReference)
    } == {
        "account_id",
        "account_type",
        "currency_code",
        "institution_reference",
    }


def test_metadata_defaults_to_empty_mapping() -> None:
    value = TransferMetadata.of()

    assert value.values == {}
    assert isinstance(value.values, MappingProxyType)


def test_metadata_normalizes_keys_and_order() -> None:
    value = TransferMetadata.of(
        {
            "Zeta Key": "last",
            "alpha-key": "first",
        }
    )

    assert list(value.values) == [
        "alpha_key",
        "zeta_key",
    ]
    assert value.values["alpha_key"] == "first"


def test_metadata_normalizes_nested_structures() -> None:
    value = TransferMetadata.of(
        {
            "corridor": {
                "Source Country": "AU",
                "destination-country": "US",
            },
            "tags": [
                "consumer",
                "international",
            ],
            "retryable": False,
            "attempt": 1,
            "optional": None,
        }
    )

    assert value.values["tags"] == (
        "consumer",
        "international",
    )
    assert value.values["corridor"]["source_country"] == "AU"
    assert value.values["corridor"]["destination_country"] == "US"
    assert value.values["retryable"] is False
    assert value.values["attempt"] == 1
    assert value.values["optional"] is None


def test_metadata_preserves_instance() -> None:
    original = TransferMetadata.of(
        {
            "channel": "mobile",
        }
    )

    assert TransferMetadata.of(original) is original


def test_metadata_is_defensively_immutable() -> None:
    source = {
        "channel": "mobile",
        "tags": [
            "consumer",
        ],
    }

    value = TransferMetadata.of(source)

    source["channel"] = "web"
    source["tags"].append("changed")

    assert value.values["channel"] == "mobile"
    assert value.values["tags"] == (
        "consumer",
    )

    with pytest.raises(TypeError):
        value.values["channel"] = "web"  # type: ignore[index]


@pytest.mark.parametrize(
    "key",
    [
        "api_key",
        "API-Key",
        "password",
        "user_password",
        "access_token",
        "authorization",
        "credentials",
        "private key",
        "pin",
        "cvv",
        "security-code",
    ],
)
def test_metadata_rejects_sensitive_keys(
    key: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        TransferMetadata.of(
            {
                key: "sensitive",
            }
        )


def test_metadata_rejects_nested_sensitive_key() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        TransferMetadata.of(
            {
                "provider": {
                    "api_key": "sensitive",
                }
            }
        )


def test_metadata_rejects_duplicate_normalized_key() -> None:
    with pytest.raises(
        ValueError,
        match="duplicate normalized key",
    ):
        TransferMetadata.of(
            {
                "channel-name": "mobile",
                "channel name": "web",
            }
        )


def test_metadata_rejects_too_many_keys() -> None:
    with pytest.raises(
        ValueError,
        match="too many keys",
    ):
        TransferMetadata.of(
            {
                f"key_{index}": index
                for index in range(65)
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        object(),
        1.5,
        {1, 2},
        b"bytes",
    ],
)
def test_metadata_rejects_unsupported_value_type(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="unsupported value type",
    ):
        TransferMetadata.of(
            {
                "value": value,
            }
        )


@pytest.mark.parametrize(
    "value",
    [
        [],
        (),
        "metadata",
        1,
        object(),
    ],
)
def test_metadata_rejects_non_mapping(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a mapping",
    ):
        TransferMetadata.of(value)


def test_metadata_canonical_dict_returns_immutable_mapping() -> None:
    value = TransferMetadata.of(
        {
            "channel": "mobile",
        }
    )

    payload = value.canonical_dict()

    assert payload is value.values

    with pytest.raises(TypeError):
        payload["channel"] = "web"  # type: ignore[index]


def test_primitives_are_immutable() -> None:
    values = (
        TransferId("transfer-001"),
        TransferReference("reference-001"),
        TransferPartyReference(
            party_id="customer-001",
            party_type="customer",
        ),
        TransferAccountReference(
            account_id="wallet-001",
            account_type="wallet",
        ),
        TransferMetadata.of(
            {
                "channel": "mobile",
            }
        ),
    )

    for value in values:
        field_name = next(
            item.name
            for item in fields(value)
        )

        with pytest.raises(FrozenInstanceError):
            setattr(value, field_name, object())


def test_transfer_primitives_contain_no_runtime_authority() -> None:
    value_types = (
        TransferId,
        TransferReference,
        TransferPartyReference,
        TransferAccountReference,
        TransferMetadata,
    )

    for value_type in value_types:
        names = {
            name
            for name in dir(value_type)
            if not name.startswith("__")
        }

        for forbidden in (
            "debit",
            "credit",
            "post",
            "settle",
            "execute",
            "send",
            "submit_to_provider",
            "fetch",
            "connect",
            "lock_rate",
            "convert",
            "save",
            "persist",
            "repository",
            "database",
        ):
            assert forbidden not in names


def test_transfer_account_reference_contains_no_balance_authority() -> None:
    field_names = {
        item.name
        for item in fields(TransferAccountReference)
    }

    for forbidden in (
        "balance",
        "available_balance",
        "ledger",
        "journal",
        "provider_client",
        "credentials",
        "database",
    ):
        assert forbidden not in field_names


def test_transfer_aggregate_is_available_in_module() -> None:
    assert hasattr(transfer, "Transfer")


def test_transfer_primitives_are_exported_from_domain() -> None:
    import afritech.novapay.domain as domain

    for symbol in transfer.__all__:
        assert getattr(domain, symbol) is getattr(
            transfer,
            symbol,
        )


def test_transfer_module_contract() -> None:
    assert transfer.__all__ == [
        "Transfer",
        "TransferAccountReference",
        "TransferAmountBreakdown",
        "TransferBeneficiaryReference",
        "TransferCharge",
        "TransferDirection",
        "TransferFee",
        "TransferFeeType",
        "TransferFundingReference",
        "TransferId",
        "TransferInstruction",
        "TransferInstructionId",
        "TransferInstructionMetadata",
        "TransferMetadata",
        "TransferPartyReference",
        "TransferPricingMetadata",
        "TransferPriority",
        "TransferPurpose",
        "TransferReference",
        "TransferStatus",
        "TransferType",
    ]
