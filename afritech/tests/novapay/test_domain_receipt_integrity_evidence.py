from __future__ import annotations

from dataclasses import (
    FrozenInstanceError,
    fields,
    is_dataclass,
)
from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import Any

import pytest

from afritech.novapay.domain.receipt import (
    ReceiptIntegrityEvidence,
    ReceiptIntegrityEvidenceType,
    ReceiptMetadata,
)


CREATED_AT = datetime(
    2026,
    8,
    5,
    1,
    0,
    tzinfo=timezone.utc,
)

EXPIRES_AT = datetime(
    2026,
    8,
    5,
    2,
    0,
    tzinfo=timezone.utc,
)


def evidence(
    **overrides: Any,
) -> ReceiptIntegrityEvidence:
    values: dict[str, Any] = {
        "evidence_type": "sha256_digest",
        "value": "abc123",
        "created_at": CREATED_AT,
        "issuer": "NovaPay",
        "expires_at": EXPIRES_AT,
        "metadata": {},
    }

    values.update(overrides)

    return ReceiptIntegrityEvidence(**values)


def test_record_is_frozen_dataclass() -> None:
    assert is_dataclass(
        ReceiptIntegrityEvidence
    )

    assert (
        ReceiptIntegrityEvidence
        .__dataclass_params__
        .frozen
        is True
    )


def test_record_field_inventory() -> None:
    assert [
        field.name
        for field in fields(
            ReceiptIntegrityEvidence
        )
    ] == [
        "evidence_type",
        "value",
        "created_at",
        "issuer",
        "expires_at",
        "metadata",
    ]


@pytest.mark.parametrize(
    "evidence_type",
    list(ReceiptIntegrityEvidenceType),
)
def test_accepts_every_integrity_evidence_type(
    evidence_type: ReceiptIntegrityEvidenceType,
) -> None:
    record = evidence(
        evidence_type=evidence_type,
    )

    assert record.evidence_type is evidence_type


@pytest.mark.parametrize(
    "evidence_type",
    list(ReceiptIntegrityEvidenceType),
)
def test_parses_normalized_evidence_type_strings(
    evidence_type: ReceiptIntegrityEvidenceType,
) -> None:
    record = evidence(
        evidence_type=(
            f" {evidence_type.value.upper()} "
        ),
    )

    assert record.evidence_type is evidence_type


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        "unknown-integrity-evidence",
        123,
        True,
        None,
    ],
)
def test_rejects_invalid_evidence_type(
    invalid: object,
) -> None:
    with pytest.raises(
        (TypeError, ValueError),
    ):
        evidence(
            evidence_type=invalid,
        )


def test_normalizes_required_value() -> None:
    record = evidence(
        value=" abc123 ",
    )

    assert record.value == "abc123"


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        123,
        True,
        None,
    ],
)
def test_rejects_invalid_required_value(
    invalid: object,
) -> None:
    with pytest.raises(
        (TypeError, ValueError),
    ):
        evidence(
            value=invalid,
        )


def test_accepts_maximum_length_value() -> None:
    value = "a" * 4096

    record = evidence(
        value=value,
    )

    assert record.value == value


def test_rejects_overlength_value() -> None:
    with pytest.raises(ValueError):
        evidence(
            value="a" * 4097,
        )


def test_normalizes_optional_issuer() -> None:
    record = evidence(
        issuer=" NovaPay ",
    )

    assert record.issuer == "NovaPay"


def test_accepts_none_issuer() -> None:
    record = evidence(
        issuer=None,
    )

    assert record.issuer is None


@pytest.mark.parametrize(
    "invalid",
    [
        "",
        " ",
        123,
        True,
    ],
)
def test_rejects_invalid_issuer(
    invalid: object,
) -> None:
    with pytest.raises(
        (TypeError, ValueError),
    ):
        evidence(
            issuer=invalid,
        )


def test_accepts_maximum_length_issuer() -> None:
    issuer = "a" * 512

    record = evidence(
        issuer=issuer,
    )

    assert record.issuer == issuer


def test_rejects_overlength_issuer() -> None:
    with pytest.raises(ValueError):
        evidence(
            issuer="a" * 513,
        )


def test_normalizes_created_at_to_utc() -> None:
    plus_ten = timezone(
        timedelta(hours=10)
    )

    local_time = datetime(
        2026,
        8,
        5,
        11,
        0,
        tzinfo=plus_ten,
    )

    record = evidence(
        created_at=local_time,
    )

    assert record.created_at == CREATED_AT
    assert record.created_at.tzinfo is timezone.utc


def test_normalizes_expiry_to_utc() -> None:
    plus_ten = timezone(
        timedelta(hours=10)
    )

    local_expiry = datetime(
        2026,
        8,
        5,
        12,
        0,
        tzinfo=plus_ten,
    )

    record = evidence(
        expires_at=local_expiry,
    )

    assert record.expires_at == EXPIRES_AT
    assert record.expires_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "expires_at",
    ],
)
def test_rejects_naive_datetimes(
    field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        evidence(
            **{
                field_name: datetime(
                    2026,
                    8,
                    5,
                    1,
                    0,
                )
            }
        )


@pytest.mark.parametrize(
    "field_name",
    [
        "created_at",
        "expires_at",
    ],
)
def test_rejects_non_datetime_values(
    field_name: str,
) -> None:
    with pytest.raises(TypeError):
        evidence(
            **{
                field_name: "2026-08-05T01:00:00Z"
            }
        )


def test_accepts_non_expiring_evidence() -> None:
    record = evidence(
        expires_at=None,
    )

    assert record.expires_at is None
    assert record.is_expiring is False
    assert record.is_expired is False


def test_rejects_expiry_before_creation() -> None:
    with pytest.raises(
        ValueError,
        match="must not precede creation",
    ):
        evidence(
            expires_at=(
                CREATED_AT
                - timedelta(microseconds=1)
            ),
        )


def test_allows_expiry_at_creation() -> None:
    record = evidence(
        expires_at=CREATED_AT,
    )

    assert record.expires_at == CREATED_AT
    assert record.is_expired_at(CREATED_AT) is True


def test_deterministic_expiry_evaluation() -> None:
    record = evidence()

    assert record.is_expired_at(
        CREATED_AT,
    ) is False

    assert record.is_expired_at(
        EXPIRES_AT - timedelta(microseconds=1),
    ) is False

    assert record.is_expired_at(
        EXPIRES_AT,
    ) is True

    assert record.is_expired_at(
        EXPIRES_AT + timedelta(microseconds=1),
    ) is True


def test_expiry_evaluation_normalizes_timezone() -> None:
    plus_ten = timezone(
        timedelta(hours=10)
    )

    local_expiry = datetime(
        2026,
        8,
        5,
        12,
        0,
        tzinfo=plus_ten,
    )

    record = evidence()

    assert record.is_expired_at(
        local_expiry,
    ) is True


def test_expiry_evaluation_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        evidence().is_expired_at(
            datetime(
                2026,
                8,
                5,
                2,
                0,
            ),
        )


def test_normalizes_mapping_metadata() -> None:
    record = evidence(
        metadata={
            "source": "provider",
            "nested": {
                "values": [1, 2],
            },
        },
    )

    assert isinstance(
        record.metadata,
        ReceiptMetadata,
    )

    assert record.metadata.canonical_dict() == {
        "source": "provider",
        "nested": {
            "values": [1, 2],
        },
    }


def test_accepts_receipt_metadata_value_object() -> None:
    metadata = ReceiptMetadata.of(
        {
            "source": "provider",
        }
    )

    record = evidence(
        metadata=metadata,
    )

    assert record.metadata == metadata


def test_default_metadata_is_empty() -> None:
    record = ReceiptIntegrityEvidence(
        evidence_type="sha256_digest",
        value="abc123",
        created_at=CREATED_AT,
    )

    assert isinstance(
        record.metadata,
        ReceiptMetadata,
    )

    assert record.metadata.canonical_dict() == {}


def test_record_is_immutable() -> None:
    record = evidence()

    with pytest.raises(FrozenInstanceError):
        record.value = "changed"


def test_canonical_serialization() -> None:
    record = evidence(
        metadata={
            "source": "receipt",
        },
    )

    assert record.canonical_dict() == {
        "evidence_type": "sha256_digest",
        "value": "abc123",
        "created_at": (
            "2026-08-05T01:00:00+00:00"
        ),
        "issuer": "NovaPay",
        "expires_at": (
            "2026-08-05T02:00:00+00:00"
        ),
        "metadata": {
            "source": "receipt",
        },
    }


def test_non_expiring_serialization() -> None:
    record = evidence(
        expires_at=None,
        issuer=None,
    )

    payload = record.canonical_dict()

    assert payload["issuer"] is None
    assert payload["expires_at"] is None


def test_serialization_is_deterministic() -> None:
    record = evidence(
        metadata={
            "source": "provider",
        },
    )

    first = record.canonical_dict()
    second = record.canonical_dict()

    assert first == second


def test_serialization_is_fresh() -> None:
    record = evidence()

    first = record.canonical_dict()
    second = record.canonical_dict()

    assert first is not second
    assert first["metadata"] is not second["metadata"]


def test_serialization_payload_is_isolated() -> None:
    record = evidence(
        metadata={
            "nested": {
                "values": [1, 2],
            },
        },
    )

    payload = record.canonical_dict()

    payload["metadata"]["nested"]["values"].append(
        3
    )

    fresh = record.canonical_dict()

    assert fresh["metadata"]["nested"]["values"] == [
        1,
        2,
    ]


def test_record_adds_no_execution_authority() -> None:
    forbidden = {
        "sign",
        "verify",
        "verify_external",
        "submit",
        "submit_provider",
        "persist",
        "save",
        "deliver",
        "execute_payment",
        "post_ledger",
    }

    public_names = {
        name
        for name in dir(
            ReceiptIntegrityEvidence
        )
        if not name.startswith("__")
    }

    assert forbidden.isdisjoint(
        public_names
    )
