from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

from afritech.novapay import (
    Currency,
    LedgerAccount,
    LedgerAccountId,
    LedgerAccountMetadata,
    LedgerAccountStatus,
    LedgerAccountType,
    NormalBalanceSide,
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


def build_account(
    *,
    account_id: LedgerAccountId | str = "ledger-account-001",
    account_code: str = "1000.CASH",
    name: str = "Consumer Cash Account",
    account_type: LedgerAccountType | str = LedgerAccountType.ASSET,
    normal_balance: NormalBalanceSide | str = NormalBalanceSide.DEBIT,
    status: LedgerAccountStatus | str = LedgerAccountStatus.PENDING,
    currency: Currency | str = "AUD",
    created_at: datetime = CREATED_AT,
    updated_at: datetime = CREATED_AT,
    owner_id: str | None = "owner-001",
    wallet_id: str | None = "wallet-001",
    tenant_id: str | None = "tenant-001",
    parent_account_id: LedgerAccountId | str | None = None,
    metadata: LedgerAccountMetadata | dict[str, object] | None = None,
    version: int = 1,
) -> LedgerAccount:
    return LedgerAccount(
        account_id=account_id,  # type: ignore[arg-type]
        account_code=account_code,
        name=name,
        account_type=account_type,  # type: ignore[arg-type]
        normal_balance=normal_balance,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        currency=currency,  # type: ignore[arg-type]
        created_at=created_at,
        updated_at=updated_at,
        owner_id=owner_id,
        wallet_id=wallet_id,
        tenant_id=tenant_id,
        parent_account_id=parent_account_id,  # type: ignore[arg-type]
        metadata=LedgerAccountMetadata.of(metadata),
        version=version,
    )


# ---------------------------------------------------------------------------
# LedgerAccountId
# ---------------------------------------------------------------------------


def test_ledger_account_id_normalizes_whitespace() -> None:
    account_id = LedgerAccountId(" ledger-account-001 ")

    assert account_id.value == "ledger-account-001"
    assert account_id.canonical() == "ledger-account-001"
    assert str(account_id) == "ledger-account-001"


def test_ledger_account_id_of_returns_existing_instance() -> None:
    account_id = LedgerAccountId("ledger-account-001")

    assert LedgerAccountId.of(account_id) is account_id


@pytest.mark.parametrize(
    "value",
    (
        "",
        " ",
        "ab",
        "ledger account",
        "ledger/account",
        "-account",
        "_account",
    ),
)
def test_ledger_account_id_rejects_invalid_values(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        LedgerAccountId(value)


def test_ledger_account_id_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="ledger account id must be a string",
    ):
        LedgerAccountId.of(123)


def test_ledger_account_id_accepts_supported_characters() -> None:
    account_id = LedgerAccountId(
        "ledger.asset_001:aud"
    )

    assert account_id.value == "ledger.asset_001:aud"


def test_ledger_account_id_is_immutable() -> None:
    account_id = LedgerAccountId("ledger-account-001")

    with pytest.raises(FrozenInstanceError):
        account_id.value = "ledger-account-002"  # type: ignore[misc]


def test_ledger_account_ids_are_orderable() -> None:
    assert (
        LedgerAccountId("ledger-account-001")
        < LedgerAccountId("ledger-account-002")
    )


# ---------------------------------------------------------------------------
# LedgerAccountType
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (" ASSET ", LedgerAccountType.ASSET),
        ("liability", LedgerAccountType.LIABILITY),
        ("EQUITY", LedgerAccountType.EQUITY),
        ("revenue", LedgerAccountType.REVENUE),
        ("expense", LedgerAccountType.EXPENSE),
        ("contra_asset", LedgerAccountType.CONTRA_ASSET),
        (
            "contra_liability",
            LedgerAccountType.CONTRA_LIABILITY,
        ),
        ("contra_equity", LedgerAccountType.CONTRA_EQUITY),
        (
            "contra_revenue",
            LedgerAccountType.CONTRA_REVENUE,
        ),
        (
            "contra_expense",
            LedgerAccountType.CONTRA_EXPENSE,
        ),
    ),
)
def test_ledger_account_type_parse_normalizes(
    raw: str,
    expected: LedgerAccountType,
) -> None:
    assert LedgerAccountType.parse(raw) is expected


def test_ledger_account_type_parse_returns_existing_enum() -> None:
    assert (
        LedgerAccountType.parse(LedgerAccountType.ASSET)
        is LedgerAccountType.ASSET
    )


def test_ledger_account_type_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="ledger account type must be a string",
    ):
        LedgerAccountType.parse(123)


def test_ledger_account_type_rejects_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="ledger account type must not be empty",
    ):
        LedgerAccountType.parse("   ")


def test_ledger_account_type_rejects_unknown_value() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported ledger account type",
    ):
        LedgerAccountType.parse("unknown")


# ---------------------------------------------------------------------------
# NormalBalanceSide
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (" DEBIT ", NormalBalanceSide.DEBIT),
        ("credit", NormalBalanceSide.CREDIT),
    ),
)
def test_normal_balance_side_parse_normalizes(
    raw: str,
    expected: NormalBalanceSide,
) -> None:
    assert NormalBalanceSide.parse(raw) is expected


def test_normal_balance_side_returns_existing_enum() -> None:
    assert (
        NormalBalanceSide.parse(NormalBalanceSide.DEBIT)
        is NormalBalanceSide.DEBIT
    )


def test_normal_balance_side_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="normal balance side must be a string",
    ):
        NormalBalanceSide.parse(123)


def test_normal_balance_side_rejects_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="normal balance side must not be empty",
    ):
        NormalBalanceSide.parse("   ")


def test_normal_balance_side_rejects_unknown_value() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported normal balance side",
    ):
        NormalBalanceSide.parse("left")


# ---------------------------------------------------------------------------
# LedgerAccountStatus
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    (
        (" PENDING ", LedgerAccountStatus.PENDING),
        ("active", LedgerAccountStatus.ACTIVE),
        ("RESTRICTED", LedgerAccountStatus.RESTRICTED),
        ("suspended", LedgerAccountStatus.SUSPENDED),
        ("closed", LedgerAccountStatus.CLOSED),
    ),
)
def test_ledger_account_status_parse_normalizes(
    raw: str,
    expected: LedgerAccountStatus,
) -> None:
    assert LedgerAccountStatus.parse(raw) is expected


def test_ledger_account_status_returns_existing_enum() -> None:
    assert (
        LedgerAccountStatus.parse(
            LedgerAccountStatus.ACTIVE
        )
        is LedgerAccountStatus.ACTIVE
    )


def test_ledger_account_status_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="ledger account status must be a string",
    ):
        LedgerAccountStatus.parse(123)


def test_ledger_account_status_rejects_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="ledger account status must not be empty",
    ):
        LedgerAccountStatus.parse("   ")


def test_ledger_account_status_rejects_unknown_value() -> None:
    with pytest.raises(
        ValueError,
        match="unsupported ledger account status",
    ):
        LedgerAccountStatus.parse("archived")


# ---------------------------------------------------------------------------
# LedgerAccountMetadata
# ---------------------------------------------------------------------------


def test_ledger_account_metadata_defaults_empty() -> None:
    metadata = LedgerAccountMetadata()

    assert dict(metadata.values) == {}


def test_ledger_account_metadata_of_none_is_empty() -> None:
    metadata = LedgerAccountMetadata.of(None)

    assert dict(metadata.values) == {}


def test_ledger_account_metadata_of_returns_existing() -> None:
    metadata = LedgerAccountMetadata(
        {"classification": "cash"}
    )

    assert LedgerAccountMetadata.of(metadata) is metadata


def test_ledger_account_metadata_normalizes_keys() -> None:
    metadata = LedgerAccountMetadata(
        {
            " classification ": "cash",
            "region": "AU",
        }
    )

    assert metadata.values == {
        "classification": "cash",
        "region": "AU",
    }


def test_ledger_account_metadata_defensive_copy() -> None:
    source = {"classification": "cash"}

    metadata = LedgerAccountMetadata(source)
    source["classification"] = "bank"

    assert metadata.get("classification") == "cash"


def test_ledger_account_metadata_mapping_is_immutable() -> None:
    metadata = LedgerAccountMetadata(
        {"classification": "cash"}
    )

    with pytest.raises(TypeError):
        metadata.values["classification"] = "bank"  # type: ignore[index]


def test_ledger_account_metadata_canonical_mapping_is_immutable() -> None:
    payload = LedgerAccountMetadata(
        {"classification": "cash"}
    ).canonical_dict()

    with pytest.raises(TypeError):
        payload["classification"] = "bank"  # type: ignore[index]


def test_ledger_account_metadata_get_default() -> None:
    metadata = LedgerAccountMetadata(
        {"classification": "cash"}
    )

    assert metadata.get("classification") == "cash"
    assert metadata.get("missing", "default") == "default"


def test_ledger_account_metadata_with_value_returns_new_value() -> None:
    original = LedgerAccountMetadata(
        {"classification": "cash"}
    )

    updated = original.with_value(" region ", "AU")

    assert original.values == {
        "classification": "cash",
    }
    assert updated.values == {
        "classification": "cash",
        "region": "AU",
    }


def test_ledger_account_metadata_without_returns_new_value() -> None:
    original = LedgerAccountMetadata(
        {
            "classification": "cash",
            "region": "AU",
        }
    )

    updated = original.without("region")

    assert original.values == {
        "classification": "cash",
        "region": "AU",
    }
    assert updated.values == {
        "classification": "cash",
    }


def test_ledger_account_metadata_without_missing_is_safe() -> None:
    metadata = LedgerAccountMetadata(
        {"classification": "cash"}
    )

    updated = metadata.without("missing")

    assert updated.values == {
        "classification": "cash",
    }


@pytest.mark.parametrize(
    "value",
    (
        [],
        "metadata",
        123,
    ),
)
def test_ledger_account_metadata_rejects_non_mapping(
    value: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="ledger account metadata must be a mapping",
    ):
        LedgerAccountMetadata.of(value)  # type: ignore[arg-type]


def test_ledger_account_metadata_rejects_non_string_key() -> None:
    with pytest.raises(
        TypeError,
        match="ledger account metadata keys must be strings",
    ):
        LedgerAccountMetadata(
            {1: "invalid"}  # type: ignore[dict-item]
        )


def test_ledger_account_metadata_rejects_empty_key() -> None:
    with pytest.raises(
        ValueError,
        match="ledger account metadata keys must not be empty",
    ):
        LedgerAccountMetadata({"   ": "invalid"})


def test_ledger_account_metadata_is_immutable() -> None:
    metadata = LedgerAccountMetadata()

    with pytest.raises(FrozenInstanceError):
        metadata.values = {}  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Construction, normalization and accounting invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("account_type", "expected_side"),
    (
        (LedgerAccountType.ASSET, NormalBalanceSide.DEBIT),
        (
            LedgerAccountType.LIABILITY,
            NormalBalanceSide.CREDIT,
        ),
        (
            LedgerAccountType.EQUITY,
            NormalBalanceSide.CREDIT,
        ),
        (
            LedgerAccountType.REVENUE,
            NormalBalanceSide.CREDIT,
        ),
        (
            LedgerAccountType.EXPENSE,
            NormalBalanceSide.DEBIT,
        ),
        (
            LedgerAccountType.CONTRA_ASSET,
            NormalBalanceSide.CREDIT,
        ),
        (
            LedgerAccountType.CONTRA_LIABILITY,
            NormalBalanceSide.DEBIT,
        ),
        (
            LedgerAccountType.CONTRA_EQUITY,
            NormalBalanceSide.DEBIT,
        ),
        (
            LedgerAccountType.CONTRA_REVENUE,
            NormalBalanceSide.DEBIT,
        ),
        (
            LedgerAccountType.CONTRA_EXPENSE,
            NormalBalanceSide.CREDIT,
        ),
    ),
)
def test_create_assigns_required_normal_balance(
    account_type: LedgerAccountType,
    expected_side: NormalBalanceSide,
) -> None:
    account = LedgerAccount.create(
        account_id=f"account-{account_type.value}",
        account_code=f"1000.{account_type.value}",
        name=f"{account_type.value} account",
        account_type=account_type,
        currency="AUD",
        created_at=CREATED_AT,
    )

    assert account.normal_balance is expected_side
    assert account.status is LedgerAccountStatus.PENDING


def test_create_normalizes_all_supported_fields() -> None:
    account = LedgerAccount.create(
        account_id=" ledger-account-001 ",
        account_code=" 1000.cash ",
        name="  Consumer   Cash   Account ",
        account_type=" ASSET ",
        currency=" aud ",
        owner_id=" owner-001 ",
        wallet_id=" wallet-001 ",
        tenant_id=" tenant-001 ",
        parent_account_id=" parent-account-001 ",
        metadata={" class ": "cash"},
        created_at=CREATED_AT,
    )

    assert account.account_id == LedgerAccountId(
        "ledger-account-001"
    )
    assert account.account_code == "1000.CASH"
    assert account.name == "Consumer Cash Account"
    assert account.account_type is LedgerAccountType.ASSET
    assert account.normal_balance is NormalBalanceSide.DEBIT
    assert account.status is LedgerAccountStatus.PENDING
    assert account.currency == Currency("AUD")
    assert account.owner_id == "owner-001"
    assert account.wallet_id == "wallet-001"
    assert account.tenant_id == "tenant-001"
    assert account.parent_account_id == LedgerAccountId(
        "parent-account-001"
    )
    assert account.metadata.values == {"class": "cash"}
    assert account.version == 1


def test_constructor_normalizes_raw_values() -> None:
    account = build_account(
        account_id=" ledger-account-001 ",
        account_code=" 1000.cash ",
        name="  Consumer   Cash Account ",
        account_type="asset",
        normal_balance="debit",
        status="pending",
        currency="aud",
    )

    assert account.account_id.value == "ledger-account-001"
    assert account.account_code == "1000.CASH"
    assert account.name == "Consumer Cash Account"
    assert account.currency.code == "AUD"


@pytest.mark.parametrize(
    ("account_type", "wrong_side"),
    (
        (LedgerAccountType.ASSET, NormalBalanceSide.CREDIT),
        (
            LedgerAccountType.LIABILITY,
            NormalBalanceSide.DEBIT,
        ),
        (
            LedgerAccountType.REVENUE,
            NormalBalanceSide.DEBIT,
        ),
        (
            LedgerAccountType.EXPENSE,
            NormalBalanceSide.CREDIT,
        ),
        (
            LedgerAccountType.CONTRA_ASSET,
            NormalBalanceSide.DEBIT,
        ),
    ),
)
def test_constructor_rejects_wrong_normal_balance(
    account_type: LedgerAccountType,
    wrong_side: NormalBalanceSide,
) -> None:
    with pytest.raises(
        ValueError,
        match="requires .* normal balance",
    ):
        build_account(
            account_type=account_type,
            normal_balance=wrong_side,
        )


@pytest.mark.parametrize(
    "value",
    (
        "",
        " ",
        "A",
        "1000 CASH",
        "/1000",
    ),
)
def test_account_code_rejects_invalid_value(
    value: str,
) -> None:
    with pytest.raises(ValueError):
        build_account(account_code=value)


def test_account_code_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="ledger account code must be a string",
    ):
        build_account(account_code=123)  # type: ignore[arg-type]


def test_account_name_collapses_whitespace() -> None:
    account = build_account(
        name=" Consumer   Cash\nAccount "
    )

    assert account.name == "Consumer Cash Account"


def test_account_name_rejects_empty_value() -> None:
    with pytest.raises(
        ValueError,
        match="ledger account name must not be empty",
    ):
        build_account(name="   ")


def test_account_name_rejects_non_string() -> None:
    with pytest.raises(
        TypeError,
        match="ledger account name must be a string",
    ):
        build_account(name=123)  # type: ignore[arg-type]


def test_account_name_rejects_more_than_160_characters() -> None:
    with pytest.raises(
        ValueError,
        match="must not exceed 160 characters",
    ):
        build_account(name="A" * 161)


def test_account_cannot_be_its_own_parent() -> None:
    with pytest.raises(
        ValueError,
        match="cannot be its own parent",
    ):
        build_account(
            account_id="ledger-account-001",
            parent_account_id="ledger-account-001",
        )


def test_optional_fields_can_be_none() -> None:
    account = build_account(
        owner_id=None,
        wallet_id=None,
        tenant_id=None,
        parent_account_id=None,
    )

    assert account.owner_id is None
    assert account.wallet_id is None
    assert account.tenant_id is None
    assert account.parent_account_id is None


def test_datetime_is_normalized_to_utc() -> None:
    plus_ten = timezone(timedelta(hours=10))
    local_time = datetime(
        2026,
        7,
        31,
        11,
        0,
        tzinfo=plus_ten,
    )

    account = LedgerAccount.create(
        account_id="ledger-account-001",
        account_code="1000.CASH",
        name="Cash Account",
        account_type="asset",
        currency="AUD",
        created_at=local_time,
    )

    assert account.created_at == CREATED_AT
    assert account.created_at.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "field_name",
    (
        "created_at",
        "updated_at",
    ),
)
def test_account_rejects_naive_datetime(
    field_name: str,
) -> None:
    values = {
        "created_at": CREATED_AT,
        "updated_at": CREATED_AT,
    }

    values[field_name] = datetime(2026, 7, 31, 1, 0)

    with pytest.raises(
        ValueError,
        match=f"ledger account {field_name} must be timezone-aware",
    ):
        build_account(**values)


def test_updated_at_cannot_precede_created_at() -> None:
    with pytest.raises(
        ValueError,
        match="updated_at must not be before created_at",
    ):
        build_account(
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
def test_account_rejects_non_integer_version(
    version: object,
) -> None:
    with pytest.raises(
        TypeError,
        match="ledger account version must be an integer",
    ):
        build_account(version=version)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "version",
    (
        0,
        -1,
    ),
)
def test_account_rejects_non_positive_version(
    version: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="ledger account version must be greater than zero",
    ):
        build_account(version=version)


def test_ledger_account_is_immutable() -> None:
    account = build_account()

    with pytest.raises(FrozenInstanceError):
        account.status = LedgerAccountStatus.ACTIVE  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------


def test_pending_account_properties() -> None:
    account = build_account()

    assert account.is_pending
    assert not account.is_active
    assert not account.is_restricted
    assert not account.is_suspended
    assert not account.is_closed
    assert not account.can_post
    assert account.is_debit_normal
    assert not account.is_credit_normal


def test_credit_normal_account_properties() -> None:
    account = build_account(
        account_type=LedgerAccountType.LIABILITY,
        normal_balance=NormalBalanceSide.CREDIT,
    )

    assert account.is_credit_normal
    assert not account.is_debit_normal


def test_activate_returns_new_version() -> None:
    original = build_account()

    active = original.activate(changed_at=CHANGED_AT)

    assert original.status is LedgerAccountStatus.PENDING
    assert original.version == 1
    assert active.status is LedgerAccountStatus.ACTIVE
    assert active.version == 2
    assert active.updated_at == CHANGED_AT
    assert active.can_post


def test_pending_can_be_restricted() -> None:
    restricted = build_account().restrict(
        changed_at=CHANGED_AT
    )

    assert restricted.is_restricted
    assert restricted.version == 2


def test_pending_can_be_closed() -> None:
    closed = build_account().close(
        changed_at=CHANGED_AT
    )

    assert closed.is_closed
    assert closed.version == 2


def test_pending_cannot_be_suspended() -> None:
    with pytest.raises(
        ValueError,
        match="pending to suspended is not allowed",
    ):
        build_account().suspend(
            changed_at=CHANGED_AT
        )


def test_active_can_be_suspended() -> None:
    active = build_account().activate(
        changed_at=CHANGED_AT
    )

    suspended = active.suspend(
        changed_at=CHANGED_AT + timedelta(hours=1)
    )

    assert suspended.is_suspended
    assert suspended.version == 3
    assert not suspended.can_post


def test_restricted_can_be_reactivated() -> None:
    restricted = build_account().restrict(
        changed_at=CHANGED_AT
    )

    active = restricted.activate(
        changed_at=CHANGED_AT + timedelta(hours=1)
    )

    assert active.is_active
    assert active.version == 3


def test_suspended_can_be_restricted() -> None:
    active = build_account().activate(
        changed_at=CHANGED_AT
    )

    suspended = active.suspend(
        changed_at=CHANGED_AT + timedelta(hours=1)
    )

    restricted = suspended.restrict(
        changed_at=CHANGED_AT + timedelta(hours=2)
    )

    assert restricted.is_restricted
    assert restricted.version == 4


def test_closed_account_has_no_transitions() -> None:
    closed = build_account().close(
        changed_at=CHANGED_AT
    )

    for target in (
        LedgerAccountStatus.PENDING,
        LedgerAccountStatus.ACTIVE,
        LedgerAccountStatus.RESTRICTED,
        LedgerAccountStatus.SUSPENDED,
    ):
        assert not closed.can_transition_to(target)


def test_same_status_transition_fails() -> None:
    with pytest.raises(
        ValueError,
        match="must change the status",
    ):
        build_account().transition_to(
            LedgerAccountStatus.PENDING,
            changed_at=CHANGED_AT,
        )


def test_transition_rejects_earlier_timestamp() -> None:
    active = build_account().activate(
        changed_at=CHANGED_AT
    )

    with pytest.raises(
        ValueError,
        match="changed_at must not be before updated_at",
    ):
        active.suspend(changed_at=CREATED_AT)


def test_can_transition_to_matches_pending_rules() -> None:
    account = build_account()

    assert account.can_transition_to("active")
    assert account.can_transition_to("restricted")
    assert account.can_transition_to("closed")
    assert not account.can_transition_to("suspended")
    assert not account.can_transition_to("pending")


# ---------------------------------------------------------------------------
# Metadata changes
# ---------------------------------------------------------------------------


def test_with_metadata_returns_new_version() -> None:
    original = build_account(
        metadata={"classification": "cash"}
    )

    updated = original.with_metadata(
        {
            "classification": "cash",
            "region": "AU",
        },
        changed_at=CHANGED_AT,
    )

    assert original.metadata.values == {
        "classification": "cash",
    }
    assert updated.metadata.values == {
        "classification": "cash",
        "region": "AU",
    }
    assert updated.version == 2
    assert updated.updated_at == CHANGED_AT


def test_with_metadata_rejects_no_change() -> None:
    account = build_account(
        metadata={"classification": "cash"}
    )

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        account.with_metadata(
            {"classification": "cash"},
            changed_at=CHANGED_AT,
        )


def test_with_metadata_rejects_earlier_timestamp() -> None:
    account = build_account(updated_at=CHANGED_AT)

    with pytest.raises(
        ValueError,
        match="changed_at must not be before updated_at",
    ):
        account.with_metadata(
            {"classification": "bank"},
            changed_at=CREATED_AT,
        )


# ---------------------------------------------------------------------------
# Canonical representation and public contract
# ---------------------------------------------------------------------------


def test_canonical_dict_contains_complete_account_state() -> None:
    account = build_account(
        parent_account_id="parent-account-001",
        metadata={
            "classification": "cash",
            "region": "AU",
        },
    )

    payload = account.canonical_dict()

    assert payload == {
        "account_id": "ledger-account-001",
        "account_code": "1000.CASH",
        "name": "Consumer Cash Account",
        "account_type": "asset",
        "normal_balance": "debit",
        "status": "pending",
        "currency": "AUD",
        "owner_id": "owner-001",
        "wallet_id": "wallet-001",
        "tenant_id": "tenant-001",
        "parent_account_id": "parent-account-001",
        "created_at": CREATED_AT.isoformat(),
        "updated_at": CREATED_AT.isoformat(),
        "version": 1,
        "metadata": {
            "classification": "cash",
            "region": "AU",
        },
    }


def test_canonical_dict_outer_mapping_is_immutable() -> None:
    payload = build_account().canonical_dict()

    with pytest.raises(TypeError):
        payload["status"] = "active"  # type: ignore[index]


def test_ledger_account_has_no_authoritative_balance() -> None:
    account = build_account()

    assert not hasattr(account, "balance")
    assert not hasattr(account, "available_balance")
    assert not hasattr(account, "current_balance")
    assert not hasattr(account, "posted_balance")


def test_top_level_exports_are_available() -> None:
    from afritech import novapay

    required = {
        "LedgerAccount",
        "LedgerAccountId",
        "LedgerAccountMetadata",
        "LedgerAccountStatus",
        "LedgerAccountType",
        "NormalBalanceSide",
    }

    for name in required:
        assert hasattr(novapay, name)
        assert name in novapay.__all__

    assert novapay.LedgerAccount is LedgerAccount
    assert novapay.LedgerAccountId is LedgerAccountId
    assert (
        novapay.LedgerAccountMetadata
        is LedgerAccountMetadata
    )
    assert (
        novapay.LedgerAccountStatus
        is LedgerAccountStatus
    )
    assert (
        novapay.LedgerAccountType
        is LedgerAccountType
    )
    assert (
        novapay.NormalBalanceSide
        is NormalBalanceSide
    )
