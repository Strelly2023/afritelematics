from __future__ import annotations

from dataclasses import FrozenInstanceError
from enum import Enum

import pytest

from afritech.novapay.domain.fx import (
    ExchangeRateId,
    ExchangeRateSource,
    ExchangeRateStatus,
    FXQuoteId,
    FXQuoteStatus,
)


@pytest.mark.parametrize(
    ("identifier_type", "raw", "expected"),
    [
        (
            ExchangeRateId,
            " exchange-rate-001 ",
            "exchange-rate-001",
        ),
        (
            FXQuoteId,
            " fx-quote-001 ",
            "fx-quote-001",
        ),
    ],
)
def test_fx_identifiers_normalize(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
    raw: str,
    expected: str,
) -> None:
    identifier = identifier_type(raw)

    assert identifier.value == expected
    assert str(identifier) == expected
    assert identifier.canonical() == expected
    assert identifier.canonical_dict() == {
        "value": expected,
    }


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
def test_fx_identifier_of_returns_existing_instance(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
) -> None:
    identifier = identifier_type("identifier-001")

    assert identifier_type.of(identifier) is identifier


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "identifier-001",
        "identifier_001",
        "identifier.001",
        "tenant:identifier-001",
        "identifier/001",
        "identifier@provider",
    ],
)
def test_fx_identifiers_accept_supported_characters(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
    value: str,
) -> None:
    assert identifier_type(value).value == value


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "\t",
        "\n",
    ],
)
def test_fx_identifiers_reject_empty_values(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        identifier_type(value)


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
        ["identifier-001"],
        {"value": "identifier-001"},
    ],
)
def test_fx_identifiers_reject_non_string_values(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        identifier_type.of(value)


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "identifier with spaces",
        "identifier#001",
        "identifier?001",
        "identifier+001",
        "-identifier",
    ],
)
def test_fx_identifiers_reject_unsupported_characters(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
    value: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="unsupported characters",
    ):
        identifier_type(value)


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
def test_fx_identifiers_reject_long_values(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
) -> None:
    with pytest.raises(
        ValueError,
        match="unsupported characters",
    ):
        identifier_type("a" * 129)


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
def test_fx_identifiers_are_immutable(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
) -> None:
    identifier = identifier_type("identifier-001")

    with pytest.raises(FrozenInstanceError):
        identifier.value = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "identifier_type",
    [
        ExchangeRateId,
        FXQuoteId,
    ],
)
def test_fx_identifiers_are_slotted(
    identifier_type: type[ExchangeRateId] | type[FXQuoteId],
) -> None:
    identifier = identifier_type("identifier-001")

    assert not hasattr(identifier, "__dict__")


def test_exchange_rate_and_quote_ids_are_distinct() -> None:
    rate_id = ExchangeRateId("identifier-001")
    quote_id = FXQuoteId("identifier-001")

    assert type(rate_id) is not type(quote_id)
    assert rate_id != quote_id


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (
            ExchangeRateSource.PROVIDER,
            "provider",
        ),
        (
            ExchangeRateSource.TREASURY,
            "treasury",
        ),
        (
            ExchangeRateSource.CENTRAL_BANK,
            "central_bank",
        ),
        (
            ExchangeRateSource.MARKET_DATA,
            "market_data",
        ),
        (
            ExchangeRateSource.PARTNER,
            "partner",
        ),
        (
            ExchangeRateSource.MANUAL,
            "manual",
        ),
        (
            ExchangeRateSource.DERIVED,
            "derived",
        ),
    ],
)
def test_exchange_rate_source_values(
    member: ExchangeRateSource,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            " PROVIDER ",
            ExchangeRateSource.PROVIDER,
        ),
        (
            "Treasury",
            ExchangeRateSource.TREASURY,
        ),
        (
            "CENTRAL_BANK",
            ExchangeRateSource.CENTRAL_BANK,
        ),
        (
            "market_data",
            ExchangeRateSource.MARKET_DATA,
        ),
        (
            "Partner",
            ExchangeRateSource.PARTNER,
        ),
        (
            "MANUAL",
            ExchangeRateSource.MANUAL,
        ),
        (
            "derived",
            ExchangeRateSource.DERIVED,
        ),
    ],
)
def test_exchange_rate_source_parse(
    raw: str,
    expected: ExchangeRateSource,
) -> None:
    assert ExchangeRateSource.parse(raw) is expected


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (
            ExchangeRateStatus.DRAFT,
            "draft",
        ),
        (
            ExchangeRateStatus.ACTIVE,
            "active",
        ),
        (
            ExchangeRateStatus.SUPERSEDED,
            "superseded",
        ),
        (
            ExchangeRateStatus.EXPIRED,
            "expired",
        ),
        (
            ExchangeRateStatus.SUSPENDED,
            "suspended",
        ),
        (
            ExchangeRateStatus.REVOKED,
            "revoked",
        ),
    ],
)
def test_exchange_rate_status_values(
    member: ExchangeRateStatus,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            " DRAFT ",
            ExchangeRateStatus.DRAFT,
        ),
        (
            "Active",
            ExchangeRateStatus.ACTIVE,
        ),
        (
            "SUPERSEDED",
            ExchangeRateStatus.SUPERSEDED,
        ),
        (
            "expired",
            ExchangeRateStatus.EXPIRED,
        ),
        (
            "Suspended",
            ExchangeRateStatus.SUSPENDED,
        ),
        (
            "REVOKED",
            ExchangeRateStatus.REVOKED,
        ),
    ],
)
def test_exchange_rate_status_parse(
    raw: str,
    expected: ExchangeRateStatus,
) -> None:
    assert ExchangeRateStatus.parse(raw) is expected


@pytest.mark.parametrize(
    ("member", "serialized"),
    [
        (
            FXQuoteStatus.PENDING,
            "pending",
        ),
        (
            FXQuoteStatus.OFFERED,
            "offered",
        ),
        (
            FXQuoteStatus.ACCEPTED,
            "accepted",
        ),
        (
            FXQuoteStatus.CONSUMED,
            "consumed",
        ),
        (
            FXQuoteStatus.EXPIRED,
            "expired",
        ),
        (
            FXQuoteStatus.CANCELLED,
            "cancelled",
        ),
        (
            FXQuoteStatus.REJECTED,
            "rejected",
        ),
    ],
)
def test_fx_quote_status_values(
    member: FXQuoteStatus,
    serialized: str,
) -> None:
    assert member.value == serialized


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            " PENDING ",
            FXQuoteStatus.PENDING,
        ),
        (
            "Offered",
            FXQuoteStatus.OFFERED,
        ),
        (
            "ACCEPTED",
            FXQuoteStatus.ACCEPTED,
        ),
        (
            "consumed",
            FXQuoteStatus.CONSUMED,
        ),
        (
            "Expired",
            FXQuoteStatus.EXPIRED,
        ),
        (
            "CANCELLED",
            FXQuoteStatus.CANCELLED,
        ),
        (
            "rejected",
            FXQuoteStatus.REJECTED,
        ),
    ],
)
def test_fx_quote_status_parse(
    raw: str,
    expected: FXQuoteStatus,
) -> None:
    assert FXQuoteStatus.parse(raw) is expected


@pytest.mark.parametrize(
    "enum_type",
    [
        ExchangeRateSource,
        ExchangeRateStatus,
        FXQuoteStatus,
    ],
)
def test_fx_enums_return_existing_instance(
    enum_type: type[
        ExchangeRateSource
        | ExchangeRateStatus
        | FXQuoteStatus
    ],
) -> None:
    member = tuple(enum_type)[0]

    assert enum_type.parse(member) is member


@pytest.mark.parametrize(
    "enum_type",
    [
        ExchangeRateSource,
        ExchangeRateStatus,
        FXQuoteStatus,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "unknown",
        "invalid",
    ],
)
def test_fx_enums_reject_invalid_values(
    enum_type: type[
        ExchangeRateSource
        | ExchangeRateStatus
        | FXQuoteStatus
    ],
    value: str,
) -> None:
    with pytest.raises(ValueError):
        enum_type.parse(value)


@pytest.mark.parametrize(
    "enum_type",
    [
        ExchangeRateSource,
        ExchangeRateStatus,
        FXQuoteStatus,
    ],
)
@pytest.mark.parametrize(
    "value",
    [
        None,
        123,
        object(),
    ],
)
def test_fx_enums_reject_non_strings(
    enum_type: type[
        ExchangeRateSource
        | ExchangeRateStatus
        | FXQuoteStatus
    ],
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        enum_type.parse(value)


@pytest.mark.parametrize(
    "enum_type",
    [
        ExchangeRateSource,
        ExchangeRateStatus,
        FXQuoteStatus,
    ],
)
def test_fx_enums_are_string_enums(
    enum_type: type[Enum],
) -> None:
    for member in enum_type:
        assert isinstance(member, str)
        assert isinstance(member.value, str)


def test_fx_module_public_contract() -> None:
    from afritech.novapay.domain import fx

    assert fx.__all__ == [
        "CurrencyPair",
        "ExchangeRate",
        "ExchangeRateId",
        "ExchangeRateSource",
        "ExchangeRateStatus",
        "ExchangeRateValue",
        "FXMetadata",
        "FXQuote",
        "FXQuoteId",
        "FXQuoteStatus",
        "FXValidityWindow",
        "RateSpread",
    ]
