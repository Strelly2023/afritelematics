from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay import (
    Currency,
    Wallet,
    WalletId,
    WalletMetadata,
    WalletStatus,
    WalletType,
)


CREATED_AT = datetime(
    2026,
    7,
    31,
    1,
    0,
    tzinfo=timezone.utc,
)

CHANGED_AT = datetime(
    2026,
    7,
    31,
    2,
    0,
    tzinfo=timezone.utc,
)


def build_wallet(
    *,
    status: WalletStatus | str = WalletStatus.PENDING,
    created_at: datetime = CREATED_AT,
    updated_at: datetime = CREATED_AT,
    metadata: WalletMetadata | dict[str, object] | None = None,
    version: int = 1,
) -> Wallet:
    return Wallet(
        wallet_id=WalletId("wallet-001"),
        owner_id="owner-001",
        wallet_type=WalletType.CONSUMER,
        status=status,
        home_currency=Currency("AUD"),
        created_at=created_at,
        updated_at=updated_at,
        tenant_id="tenant-001",
        external_reference="external-001",
        metadata=WalletMetadata.of(metadata),
        version=version,
    )


# ---------------------------------------------------------------------------
# WalletId
# ---------------------------------------------------------------------------


def test_wallet_id_normalizes_surrounding_whitespace() -> None:
    wallet_id = WalletId(" wallet-001 ")

    assert wallet_id.value == "wallet-001"
    assert wallet_id.canonical() == "wallet-001"
    assert str(wallet_id) == "wallet-001"


def test_wallet_id_of_returns_existing_instance() -> None:
    wallet_id = WalletId("wallet-001")

    assert WalletId.of(wallet_id) is wallet_id


@pytest.mark.parametrize(
    "value",
    (
        "",
        "   ",
        "ab",
        "wallet id",
        "wallet/001",
        "-wallet",
        "_wallet",
    ),
)
def test_wallet_id_rejects_invalid_values(value: str) -> None:
    with pytest.raises(ValueError):
        WalletId(value)


def test_wallet_id_rejects_non_string_value() -> None:
    with pytest.raises(
        TypeError,
        match="wallet id must be a string",
    ):
        WalletId.of(123)


def test_wallet_id_accepts_supported_identifier_characters() -> None:
    wallet_id = WalletId("wallet.customer_01:primary")

    assert wallet_id.value == "wallet.customer_01:primary"


def test_wallet_id_is_immutable() -> None:
    wallet_id = WalletId("wallet-001")

    with pytest.raises(FrozenInstanceError):
        wallet_id.value = "wallet-002"  # type: ignore[misc]


def test_wallet_ids_are_orderable() -> None:
    assert WalletId("wallet-001") < WalletId("wallet-002")


# ---------------------------------------------------------------------------
# WalletType
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (" CONSUMER ", WalletType.CONSUMER),
        ("agent", WalletType.AGENT),
        ("MERCHANT", WalletType.MERCHANT),
        ("business", WalletType.BUSINESS),
        ("driver", WalletType.DRIVER),
        ("fleet", WalletType.FLEET),
        ("platform", WalletType.PLATFORM),
        ("treasury", WalletType.TREASURY),
        ("escrow", WalletType.ESCROW),
        ("settlement", WalletType.SETTLEMENT),
    ),
)
def test_wallet_type_parse_normalizes_values(
    raw: str,
    expected: WalletType,
) -> None:
    assert WalletType.parse(raw) is expected


def test_wallet_type_parse_returns_existing_enum() -> None:
    assert (
        WalletType.parse(WalletType.CONSUMER)
        is WalletType.CONSUMER
    )


def test_wallet_type_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="wallet type must be a string",
    ):
        WalletType.parse(123)


def test_wallet_type_rejects_empty_string() -> None:
    with pytest.raises(
        ValueError,
        match="wallet type must not be empty",
    ):
        WalletType.parse("   ")


def test_wallet_type_rejects_unsupported_value() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported wallet type",
    ):
        WalletType.parse("unknown")


# ---------------------------------------------------------------------------
# WalletStatus
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (" PENDING ", WalletStatus.PENDING),
        ("active", WalletStatus.ACTIVE),
        ("RESTRICTED", WalletStatus.RESTRICTED),
        ("suspended", WalletStatus.SUSPENDED),
        ("closed", WalletStatus.CLOSED),
    ),
)
def test_wallet_status_parse_normalizes_values(
    raw: str,
    expected: WalletStatus,
) -> None:
    assert WalletStatus.parse(raw) is expected


def test_wallet_status_parse_returns_existing_enum() -> None:
    assert (
        WalletStatus.parse(WalletStatus.ACTIVE)
        is WalletStatus.ACTIVE
    )


def test_wallet_status_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="wallet status must be a string",
    ):
        WalletStatus.parse(123)


def test_wallet_status_rejects_empty_string() -> None:
    with pytest.raises(
        ValueError,
        match="wallet status must not be empty",
    ):
        WalletStatus.parse("   ")


def test_wallet_status_rejects_unsupported_value() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported wallet status",
    ):
        WalletStatus.parse("archived")


# ---------------------------------------------------------------------------
# WalletMetadata
# ---------------------------------------------------------------------------


def test_wallet_metadata_defaults_to_empty_mapping() -> None:
    metadata = WalletMetadata()

    assert dict(metadata.values) == {}


def test_wallet_metadata_of_none_returns_empty_metadata() -> None:
    metadata = WalletMetadata.of(None)

    assert dict(metadata.values) == {}


def test_wallet_metadata_of_returns_existing_instance() -> None:
    metadata = WalletMetadata({"channel": "mobile"})

    assert WalletMetadata.of(metadata) is metadata


def test_wallet_metadata_normalizes_keys() -> None:
    metadata = WalletMetadata(
        {
            " channel ": "mobile",
            "region": "AU",
        }
    )

    assert metadata.values == {
        "channel": "mobile",
        "region": "AU",
    }


def test_wallet_metadata_defensively_copies_source() -> None:
    source = {
        "channel": "mobile",
    }

    metadata = WalletMetadata(source)
    source["channel"] = "agent"

    assert metadata.get("channel") == "mobile"


def test_wallet_metadata_mapping_is_immutable() -> None:
    metadata = WalletMetadata({"channel": "mobile"})

    with pytest.raises(TypeError):
        metadata.values["channel"] = "agent"  # type: ignore[index]


def test_wallet_metadata_canonical_dict_is_immutable() -> None:
    payload = WalletMetadata(
        {"channel": "mobile"}
    ).canonical_dict()

    assert payload == {"channel": "mobile"}

    with pytest.raises(TypeError):
        payload["channel"] = "agent"  # type: ignore[index]


def test_wallet_metadata_get_supports_default() -> None:
    metadata = WalletMetadata({"channel": "mobile"})

    assert metadata.get("channel") == "mobile"
    assert metadata.get("missing", "default") == "default"


def test_wallet_metadata_with_value_returns_new_instance() -> None:
    original = WalletMetadata({"channel": "mobile"})
    updated = original.with_value(" region ", "AU")

    assert original.values == {"channel": "mobile"}
    assert updated.values == {
        "channel": "mobile",
        "region": "AU",
    }


def test_wallet_metadata_without_returns_new_instance() -> None:
    original = WalletMetadata(
        {
            "channel": "mobile",
            "region": "AU",
        }
    )

    updated = original.without("region")

    assert original.values == {
        "channel": "mobile",
        "region": "AU",
    }
    assert updated.values == {"channel": "mobile"}


def test_wallet_metadata_without_missing_key_is_safe() -> None:
    metadata = WalletMetadata({"channel": "mobile"})

    updated = metadata.without("missing")

    assert updated.values == {"channel": "mobile"}


@pytest.mark.parametrize(
    "value",
    (
        [],
        "metadata",
        123,
    ),
)
def test_wallet_metadata_rejects_non_mapping(value: object) -> None:
    with pytest.raises(
        TypeError,
        match="wallet metadata must be a mapping",
    ):
        WalletMetadata.of(value)  # type: ignore[arg-type]


def test_wallet_metadata_rejects_non_string_key() -> None:
    with pytest.raises(
        TypeError,
        match="wallet metadata keys must be strings",
    ):
        WalletMetadata({1: "invalid"})  # type: ignore[dict-item]


def test_wallet_metadata_rejects_empty_key() -> None:
    with pytest.raises(
        ValueError,
        match="wallet metadata keys must not be empty",
    ):
        WalletMetadata({"   ": "invalid"})


@pytest.mark.parametrize(
    "method_name",
    (
        "with_value",
        "without",
    ),
)
def test_wallet_metadata_methods_reject_non_string_key(
    method_name: str,
) -> None:
    metadata = WalletMetadata()

    method = getattr(metadata, method_name)

    with pytest.raises(
        TypeError,
        match="wallet metadata key must be a string",
    ):
        if method_name == "with_value":
            method(123, "value")
        else:
            method(123)


@pytest.mark.parametrize(
    "method_name",
    (
        "with_value",
        "without",
    ),
)
def test_wallet_metadata_methods_reject_empty_key(
    method_name: str,
) -> None:
    metadata = WalletMetadata()

    method = getattr(metadata, method_name)

    with pytest.raises(
        ValueError,
        match="wallet metadata key must not be empty",
    ):
        if method_name == "with_value":
            method("   ", "value")
        else:
            method("   ")


def test_wallet_metadata_is_immutable() -> None:
    metadata = WalletMetadata({"channel": "mobile"})

    with pytest.raises(FrozenInstanceError):
        metadata.values = {}  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Wallet construction and normalization
# ---------------------------------------------------------------------------


def test_wallet_create_builds_pending_wallet() -> None:
    wallet = Wallet.create(
        wallet_id=" wallet-001 ",
        owner_id=" owner-001 ",
        wallet_type=" CONSUMER ",
        home_currency=" aud ",
        tenant_id=" tenant-001 ",
        external_reference=" external-001 ",
        metadata={" channel ": "mobile"},
        created_at=CREATED_AT,
    )

    assert wallet.wallet_id == WalletId("wallet-001")
    assert wallet.owner_id == "owner-001"
    assert wallet.wallet_type is WalletType.CONSUMER
    assert wallet.status is WalletStatus.PENDING
    assert wallet.home_currency == Currency("AUD")
    assert wallet.tenant_id == "tenant-001"
    assert wallet.external_reference == "external-001"
    assert wallet.metadata.values == {"channel": "mobile"}
    assert wallet.created_at == CREATED_AT
    assert wallet.updated_at == CREATED_AT
    assert wallet.version == 1


def test_wallet_create_without_optional_values() -> None:
    wallet = Wallet.create(
        wallet_id="wallet-001",
        owner_id="owner-001",
        wallet_type="consumer",
        home_currency="AUD",
        created_at=CREATED_AT,
    )

    assert wallet.tenant_id is None
    assert wallet.external_reference is None
    assert wallet.metadata.values == {}


def test_wallet_constructor_normalizes_raw_values() -> None:
    wallet = Wallet(
        wallet_id=" wallet-001 ",  # type: ignore[arg-type]
        owner_id=" owner-001 ",
        wallet_type=" CONSUMER ",  # type: ignore[arg-type]
        status=" PENDING ",  # type: ignore[arg-type]
        home_currency=" aud ",  # type: ignore[arg-type]
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        metadata={" channel ": "mobile"},  # type: ignore[arg-type]
    )

    assert wallet.wallet_id == WalletId("wallet-001")
    assert wallet.owner_id == "owner-001"
    assert wallet.wallet_type is WalletType.CONSUMER
    assert wallet.status is WalletStatus.PENDING
    assert wallet.home_currency == Currency("AUD")
    assert wallet.metadata.values == {"channel": "mobile"}


def test_wallet_normalizes_datetime_to_utc() -> None:
    plus_ten = timezone(timedelta(hours=10))
    local_time = datetime(
        2026,
        7,
        31,
        11,
        0,
        tzinfo=plus_ten,
    )

    wallet = Wallet.create(
        wallet_id="wallet-001",
        owner_id="owner-001",
        wallet_type="consumer",
        home_currency="AUD",
        created_at=local_time,
    )

    assert wallet.created_at == CREATED_AT
    assert wallet.created_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "field_name",
    (
        "created_at",
        "updated_at",
    ),
)
def test_wallet_rejects_non_datetime_timestamps(
    field_name: str,
) -> None:
    values = {
        "wallet_id": WalletId("wallet-001"),
        "owner_id": "owner-001",
        "wallet_type": WalletType.CONSUMER,
        "status": WalletStatus.PENDING,
        "home_currency": Currency("AUD"),
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }

    values[field_name] = "invalid"

    with pytest.raises(
        TypeError,
        match=f"wallet {field_name} must be a datetime",
    ):
        Wallet(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "field_name",
    (
        "created_at",
        "updated_at",
    ),
)
def test_wallet_rejects_naive_timestamps(
    field_name: str,
) -> None:
    values = {
        "wallet_id": WalletId("wallet-001"),
        "owner_id": "owner-001",
        "wallet_type": WalletType.CONSUMER,
        "status": WalletStatus.PENDING,
        "home_currency": Currency("AUD"),
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }

    values[field_name] = datetime(2026, 7, 31, 1, 0)

    with pytest.raises(
        ValueError,
        match=f"wallet {field_name} must be timezone-aware",
    ):
        Wallet(**values)  # type: ignore[arg-type]


def test_wallet_rejects_updated_at_before_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="updated_at must not be before created_at",
    ):
        build_wallet(
            created_at=CHANGED_AT,
            updated_at=CREATED_AT,
        )


@pytest.mark.parametrize(
    "version",
    (
        True,
        1.5,
        "1",
    ),
)
def test_wallet_rejects_non_integer_version(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="wallet version must be an integer",
    ):
        build_wallet(version=version)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "version",
    (
        0,
        -1,
    ),
)
def test_wallet_rejects_non_positive_version(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="wallet version must be greater than zero",
    ):
        build_wallet(version=version)


def test_wallet_is_immutable() -> None:
    wallet = build_wallet()

    with pytest.raises(FrozenInstanceError):
        wallet.status = WalletStatus.ACTIVE  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Wallet lifecycle
# ---------------------------------------------------------------------------


def test_pending_wallet_properties() -> None:
    wallet = build_wallet()

    assert wallet.is_pending is True
    assert wallet.is_active is False
    assert wallet.is_restricted is False
    assert wallet.is_suspended is False
    assert wallet.is_closed is False
    assert wallet.can_transact is False


def test_active_wallet_can_transact() -> None:
    wallet = build_wallet().activate(
        changed_at=CHANGED_AT,
    )

    assert wallet.is_active is True
    assert wallet.can_transact is True


def test_activate_returns_new_version() -> None:
    original = build_wallet()
    activated = original.activate(changed_at=CHANGED_AT)

    assert original.status is WalletStatus.PENDING
    assert original.version == 1
    assert activated.status is WalletStatus.ACTIVE
    assert activated.updated_at == CHANGED_AT
    assert activated.version == 2


def test_pending_wallet_can_be_restricted() -> None:
    restricted = build_wallet().restrict(
        changed_at=CHANGED_AT,
    )

    assert restricted.status is WalletStatus.RESTRICTED
    assert restricted.version == 2


def test_pending_wallet_can_be_closed() -> None:
    closed = build_wallet().close(
        changed_at=CHANGED_AT,
    )

    assert closed.status is WalletStatus.CLOSED
    assert closed.version == 2


def test_pending_wallet_cannot_be_suspended() -> None:
    with pytest.raises(
        ValueError,
        match="pending to suspended is not allowed",
    ):
        build_wallet().suspend(changed_at=CHANGED_AT)


def test_active_wallet_can_be_suspended() -> None:
    active = build_wallet().activate(
        changed_at=CHANGED_AT,
    )

    suspended = active.suspend(
        changed_at=CHANGED_AT + timedelta(hours=1),
    )

    assert suspended.status is WalletStatus.SUSPENDED
    assert suspended.version == 3


def test_restricted_wallet_can_be_reactivated() -> None:
    restricted = build_wallet().restrict(
        changed_at=CHANGED_AT,
    )

    active = restricted.activate(
        changed_at=CHANGED_AT + timedelta(hours=1),
    )

    assert active.status is WalletStatus.ACTIVE
    assert active.version == 3


def test_suspended_wallet_can_be_restricted() -> None:
    active = build_wallet().activate(
        changed_at=CHANGED_AT,
    )

    suspended = active.suspend(
        changed_at=CHANGED_AT + timedelta(hours=1),
    )

    restricted = suspended.restrict(
        changed_at=CHANGED_AT + timedelta(hours=2),
    )

    assert restricted.status is WalletStatus.RESTRICTED
    assert restricted.version == 4


def test_closed_wallet_has_no_allowed_transitions() -> None:
    closed = build_wallet().close(
        changed_at=CHANGED_AT,
    )

    for target in (
        WalletStatus.PENDING,
        WalletStatus.ACTIVE,
        WalletStatus.RESTRICTED,
        WalletStatus.SUSPENDED,
    ):
        assert closed.can_transition_to(target) is False


def test_transition_to_same_status_fails() -> None:
    wallet = build_wallet()

    with pytest.raises(
        ValueError,
        match="must change the status",
    ):
        wallet.transition_to(
            WalletStatus.PENDING,
            changed_at=CHANGED_AT,
        )


def test_transition_rejects_timestamp_before_updated_at() -> None:
    active = build_wallet().activate(
        changed_at=CHANGED_AT,
    )

    with pytest.raises(
        ValueError,
        match="changed_at must not be before updated_at",
    ):
        active.suspend(changed_at=CREATED_AT)


def test_transition_rejects_naive_changed_at() -> None:
    with pytest.raises(
        ValueError,
        match="wallet changed_at must be timezone-aware",
    ):
        build_wallet().activate(
            changed_at=datetime(2026, 7, 31, 2, 0),
        )


def test_can_transition_to_matches_pending_rules() -> None:
    wallet = build_wallet()

    assert wallet.can_transition_to(WalletStatus.ACTIVE)
    assert wallet.can_transition_to("restricted")
    assert wallet.can_transition_to(WalletStatus.CLOSED)
    assert not wallet.can_transition_to(WalletStatus.SUSPENDED)
    assert not wallet.can_transition_to(WalletStatus.PENDING)


# ---------------------------------------------------------------------------
# Metadata updates
# ---------------------------------------------------------------------------


def test_with_metadata_returns_new_wallet_version() -> None:
    original = build_wallet(metadata={"channel": "mobile"})

    updated = original.with_metadata(
        {
            "channel": "agent",
            "region": "AU",
        },
        changed_at=CHANGED_AT,
    )

    assert original.metadata.values == {
        "channel": "mobile",
    }
    assert updated.metadata.values == {
        "channel": "agent",
        "region": "AU",
    }
    assert updated.updated_at == CHANGED_AT
    assert updated.version == 2


def test_with_metadata_rejects_unchanged_metadata() -> None:
    wallet = build_wallet(metadata={"channel": "mobile"})

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        wallet.with_metadata(
            {"channel": "mobile"},
            changed_at=CHANGED_AT,
        )


def test_with_metadata_rejects_timestamp_before_updated_at() -> None:
    wallet = build_wallet(
        updated_at=CHANGED_AT,
    )

    with pytest.raises(
        ValueError,
        match="changed_at must not be before updated_at",
    ):
        wallet.with_metadata(
            {"channel": "agent"},
            changed_at=CREATED_AT,
        )


# ---------------------------------------------------------------------------
# Canonical serialization and exports
# ---------------------------------------------------------------------------


def test_wallet_canonical_dict() -> None:
    wallet = build_wallet(
        metadata={
            "channel": "mobile",
            "region": "AU",
        }
    )

    payload = wallet.canonical_dict()

    assert payload == {
        "wallet_id": "wallet-001",
        "owner_id": "owner-001",
        "wallet_type": "consumer",
        "status": "pending",
        "home_currency": "AUD",
        "tenant_id": "tenant-001",
        "external_reference": "external-001",
        "created_at": CREATED_AT.isoformat(),
        "updated_at": CREATED_AT.isoformat(),
        "version": 1,
        "metadata": {
            "channel": "mobile",
            "region": "AU",
        },
    }


def test_wallet_canonical_dict_outer_mapping_is_immutable() -> None:
    payload = build_wallet().canonical_dict()

    with pytest.raises(TypeError):
        payload["status"] = "active"  # type: ignore[index]


def test_wallet_has_no_authoritative_balance_field() -> None:
    wallet = build_wallet()

    assert not hasattr(wallet, "balance")
    assert not hasattr(wallet, "available_balance")
    assert not hasattr(wallet, "ledger_balance")


def test_top_level_wallet_exports_are_available() -> None:
    from afritech import novapay

    required = {
        "Wallet",
        "WalletId",
        "WalletMetadata",
        "WalletStatus",
        "WalletType",
    }

    for name in required:
        assert hasattr(novapay, name)
        assert name in novapay.__all__

    assert novapay.Wallet is Wallet
    assert novapay.WalletId is WalletId
    assert novapay.WalletMetadata is WalletMetadata
    assert novapay.WalletStatus is WalletStatus
    assert novapay.WalletType is WalletType
