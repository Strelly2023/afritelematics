from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from afritech.novapay.domain.fx import (
    CurrencyPair,
    ExchangeRate,
    ExchangeRateSource,
    ExchangeRateStatus,
    ExchangeRateValue,
    FXMetadata,
    FXValidityWindow,
    RateSpread,
)


NOW = datetime(
    2026,
    8,
    2,
    6,
    0,
    tzinfo=timezone.utc,
)
LATER = NOW + timedelta(minutes=1)
EXPIRES = NOW + timedelta(minutes=10)
AFTER_EXPIRY = EXPIRES + timedelta(seconds=1)


def validity() -> FXValidityWindow:
    return FXValidityWindow(
        valid_from=NOW,
        expires_at=EXPIRES,
    )


def draft_rate() -> ExchangeRate:
    return ExchangeRate.create(
        exchange_rate_id="exchange-rate-001",
        pair=CurrencyPair.of("AUD", "USD"),
        rate=ExchangeRateValue("0.66"),
        spread=RateSpread("25"),
        source=ExchangeRateSource.PROVIDER,
        status=ExchangeRateStatus.DRAFT,
        provider="AfriPay FX",
        provider_reference="fxlock-001",
        validity=validity(),
        metadata={
            "corridor": "AU-US",
        },
        occurred_at=NOW,
    )


def active_rate() -> ExchangeRate:
    return draft_rate().publish(
        reason="approved",
        occurred_at=LATER,
    )


def suspended_rate() -> ExchangeRate:
    return active_rate().suspend(
        reason="provider review",
        occurred_at=LATER + timedelta(minutes=1),
    )


def assert_identity_preserved(
    before: ExchangeRate,
    after: ExchangeRate,
) -> None:
    assert (
        after.exchange_rate_id
        == before.exchange_rate_id
    )
    assert after.pair == before.pair
    assert after.source is before.source
    assert after.provider == before.provider
    assert after.created_at == before.created_at


def assert_new_version(
    before: ExchangeRate,
    after: ExchangeRate,
    *,
    occurred_at: datetime,
) -> None:
    assert after is not before
    assert after.version == before.version + 1
    assert after.updated_at == occurred_at
    assert_identity_preserved(before, after)


def test_publish_draft_rate() -> None:
    original = draft_rate()

    published = original.publish(
        reason="treasury approval",
        occurred_at=LATER,
    )

    assert original.status is ExchangeRateStatus.DRAFT
    assert published.status is ExchangeRateStatus.ACTIVE
    assert published.metadata.values[
        "lifecycle_action"
    ] == "publish"
    assert published.metadata.values[
        "lifecycle_reason"
    ] == "treasury approval"
    assert_new_version(
        original,
        published,
        occurred_at=LATER,
    )


@pytest.mark.parametrize(
    "status",
    [
        ExchangeRateStatus.ACTIVE,
        ExchangeRateStatus.SUSPENDED,
        ExchangeRateStatus.SUPERSEDED,
        ExchangeRateStatus.EXPIRED,
        ExchangeRateStatus.REVOKED,
    ],
)
def test_publish_rejects_non_draft(
    status: ExchangeRateStatus,
) -> None:
    rate = draft_rate()

    if status is ExchangeRateStatus.ACTIVE:
        rate = active_rate()
    elif status is ExchangeRateStatus.SUSPENDED:
        rate = suspended_rate()
    elif status is ExchangeRateStatus.SUPERSEDED:
        rate = active_rate().supersede(
            reason="replacement",
            occurred_at=LATER + timedelta(minutes=1),
        )
    elif status is ExchangeRateStatus.EXPIRED:
        rate = draft_rate().expire(
            occurred_at=AFTER_EXPIRY,
        )
    else:
        rate = draft_rate().revoke(
            reason="invalid source",
            occurred_at=LATER,
        )

    with pytest.raises(ValueError):
        rate.publish(
            occurred_at=rate.updated_at,
        )


def test_publish_requires_active_validity() -> None:
    rate = draft_rate()

    with pytest.raises(
        ValueError,
        match="active validity window",
    ):
        rate.publish(
            occurred_at=AFTER_EXPIRY,
        )


def test_suspend_active_rate() -> None:
    rate = active_rate()
    occurred_at = LATER + timedelta(minutes=1)

    suspended = rate.suspend(
        reason="provider outage",
        occurred_at=occurred_at,
    )

    assert suspended.status is ExchangeRateStatus.SUSPENDED
    assert suspended.metadata.values[
        "lifecycle_action"
    ] == "suspend"
    assert_new_version(
        rate,
        suspended,
        occurred_at=occurred_at,
    )


def test_suspend_rejects_non_active() -> None:
    with pytest.raises(
        ValueError,
        match="requires active status",
    ):
        draft_rate().suspend(
            reason="invalid",
            occurred_at=LATER,
        )


def test_resume_suspended_rate() -> None:
    rate = suspended_rate()
    occurred_at = LATER + timedelta(minutes=2)

    resumed = rate.resume(
        reason="provider recovered",
        occurred_at=occurred_at,
    )

    assert resumed.status is ExchangeRateStatus.ACTIVE
    assert resumed.metadata.values[
        "lifecycle_action"
    ] == "resume"
    assert_new_version(
        rate,
        resumed,
        occurred_at=occurred_at,
    )


def test_resume_requires_active_validity() -> None:
    rate = suspended_rate()

    with pytest.raises(
        ValueError,
        match="active validity window",
    ):
        rate.resume(
            occurred_at=AFTER_EXPIRY,
        )


def test_resume_rejects_non_suspended() -> None:
    with pytest.raises(
        ValueError,
        match="requires suspended status",
    ):
        active_rate().resume(
            occurred_at=LATER,
        )


def test_supersede_active_rate() -> None:
    rate = active_rate()
    occurred_at = LATER + timedelta(minutes=1)

    superseded = rate.supersede(
        reason="newer market rate",
        occurred_at=occurred_at,
    )

    assert superseded.status is (
        ExchangeRateStatus.SUPERSEDED
    )
    assert superseded.metadata.values[
        "lifecycle_action"
    ] == "supersede"
    assert_new_version(
        rate,
        superseded,
        occurred_at=occurred_at,
    )


def test_supersede_rejects_non_active() -> None:
    with pytest.raises(
        ValueError,
        match="requires active status",
    ):
        draft_rate().supersede(
            reason="replacement",
            occurred_at=LATER,
        )


@pytest.mark.parametrize(
    "factory",
    [
        draft_rate,
        active_rate,
        suspended_rate,
    ],
)
def test_expire_non_terminal_rate(
    factory: object,
) -> None:
    rate = factory()  # type: ignore[operator]

    expired = rate.expire(
        reason="validity ended",
        occurred_at=AFTER_EXPIRY,
    )

    assert expired.status is ExchangeRateStatus.EXPIRED
    assert expired.metadata.values[
        "lifecycle_action"
    ] == "expire"
    assert_new_version(
        rate,
        expired,
        occurred_at=AFTER_EXPIRY,
    )


def test_expire_rejects_early_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="cannot expire before",
    ):
        draft_rate().expire(
            occurred_at=LATER,
        )


@pytest.mark.parametrize(
    "factory",
    [
        draft_rate,
        active_rate,
        suspended_rate,
    ],
)
def test_revoke_allowed_statuses(
    factory: object,
) -> None:
    rate = factory()  # type: ignore[operator]
    occurred_at = max(
        rate.updated_at,
        LATER + timedelta(minutes=2),
    )

    revoked = rate.revoke(
        reason="rate integrity failure",
        occurred_at=occurred_at,
    )

    assert revoked.status is ExchangeRateStatus.REVOKED
    assert revoked.metadata.values[
        "lifecycle_action"
    ] == "revoke"
    assert_new_version(
        rate,
        revoked,
        occurred_at=occurred_at,
    )


@pytest.mark.parametrize(
    "method_name",
    [
        "suspend",
        "supersede",
        "revoke",
    ],
)
def test_required_reason_rejects_empty(
    method_name: str,
) -> None:
    rate = active_rate()
    method = getattr(rate, method_name)

    with pytest.raises(
        ValueError,
        match="reason must not be empty",
    ):
        method(
            reason=" ",
            occurred_at=rate.updated_at,
        )


@pytest.mark.parametrize(
    "terminal_status",
    [
        ExchangeRateStatus.SUPERSEDED,
        ExchangeRateStatus.EXPIRED,
        ExchangeRateStatus.REVOKED,
    ],
)
def test_terminal_states_reject_changes(
    terminal_status: ExchangeRateStatus,
) -> None:
    if terminal_status is ExchangeRateStatus.SUPERSEDED:
        rate = active_rate().supersede(
            reason="replacement",
            occurred_at=LATER + timedelta(minutes=1),
        )
    elif terminal_status is ExchangeRateStatus.EXPIRED:
        rate = draft_rate().expire(
            occurred_at=AFTER_EXPIRY,
        )
    else:
        rate = draft_rate().revoke(
            reason="invalid source",
            occurred_at=LATER,
        )

    operations = (
        lambda: rate.update_metadata(
            {"source": "manual"},
            occurred_at=rate.updated_at,
        ),
        lambda: rate.revoke(
            reason="again",
            occurred_at=rate.updated_at,
        ),
        lambda: rate.expire(
            occurred_at=max(
                rate.updated_at,
                AFTER_EXPIRY,
            ),
        ),
    )

    for operation in operations:
        with pytest.raises(
            ValueError,
            match="terminal exchange rate",
        ):
            operation()


def test_update_rate_on_draft() -> None:
    rate = draft_rate()

    updated = rate.update_rate(
        "0.67",
        occurred_at=LATER,
    )

    assert rate.rate.rate == Decimal("0.66")
    assert updated.rate.rate == Decimal("0.67")
    assert_new_version(
        rate,
        updated,
        occurred_at=LATER,
    )


def test_update_rate_rejects_no_op() -> None:
    rate = draft_rate()

    with pytest.raises(
        ValueError,
        match="must change rate",
    ):
        rate.update_rate(
            rate.rate,
            occurred_at=LATER,
        )


def test_update_spread_on_draft() -> None:
    rate = draft_rate()

    updated = rate.update_spread(
        "50",
        occurred_at=LATER,
    )

    assert rate.spread.basis_points == Decimal("25")
    assert updated.spread.basis_points == Decimal("50")
    assert_new_version(
        rate,
        updated,
        occurred_at=LATER,
    )


def test_update_spread_rejects_no_op() -> None:
    rate = draft_rate()

    with pytest.raises(
        ValueError,
        match="must change spread",
    ):
        rate.update_spread(
            rate.spread,
            occurred_at=LATER,
        )


def test_update_validity_on_draft() -> None:
    rate = draft_rate()
    new_validity = FXValidityWindow(
        valid_from=NOW,
        expires_at=EXPIRES + timedelta(minutes=5),
    )

    updated = rate.update_validity(
        new_validity,
        occurred_at=LATER,
    )

    assert updated.validity == new_validity
    assert_new_version(
        rate,
        updated,
        occurred_at=LATER,
    )


def test_update_validity_requires_window() -> None:
    with pytest.raises(
        TypeError,
        match="FXValidityWindow",
    ):
        draft_rate().update_validity(
            {
                "valid_from": NOW,
                "expires_at": EXPIRES,
            },  # type: ignore[arg-type]
            occurred_at=LATER,
        )


def test_update_provider_reference_on_draft() -> None:
    rate = draft_rate()

    updated = rate.update_provider_reference(
        " fxlock-002 ",
        occurred_at=LATER,
    )

    assert updated.provider_reference == "fxlock-002"
    assert_new_version(
        rate,
        updated,
        occurred_at=LATER,
    )


@pytest.mark.parametrize(
    "method_name",
    [
        "update_rate",
        "update_spread",
        "update_validity",
        "update_provider_reference",
    ],
)
def test_pricing_updates_reject_non_draft(
    method_name: str,
) -> None:
    rate = active_rate()
    method = getattr(rate, method_name)

    arguments = {
        "update_rate": "0.67",
        "update_spread": "50",
        "update_validity": FXValidityWindow(
            valid_from=NOW,
            expires_at=EXPIRES + timedelta(minutes=5),
        ),
        "update_provider_reference": "fxlock-002",
    }

    with pytest.raises(
        ValueError,
        match="require draft status",
    ):
        method(
            arguments[method_name],
            occurred_at=rate.updated_at,
        )


def test_update_metadata_on_draft() -> None:
    rate = draft_rate()

    updated = rate.update_metadata(
        {
            "corridor": "AU-US",
            "rate_type": "wholesale",
        },
        occurred_at=LATER,
    )

    assert updated.metadata.values == {
        "corridor": "AU-US",
        "rate_type": "wholesale",
    }
    assert_new_version(
        rate,
        updated,
        occurred_at=LATER,
    )


def test_update_metadata_on_active() -> None:
    rate = active_rate()
    occurred_at = LATER + timedelta(minutes=1)

    updated = rate.update_metadata(
        {
            "monitoring_reference": "monitor-001",
        },
        occurred_at=occurred_at,
    )

    assert updated.status is ExchangeRateStatus.ACTIVE
    assert updated.metadata.values == {
        "monitoring_reference": "monitor-001",
    }
    assert_new_version(
        rate,
        updated,
        occurred_at=occurred_at,
    )


def test_update_metadata_rejects_sensitive_key() -> None:
    with pytest.raises(
        ValueError,
        match="prohibited sensitive key",
    ):
        draft_rate().update_metadata(
            {"access_token": "secret"},
            occurred_at=LATER,
        )


def test_update_metadata_rejects_no_op() -> None:
    rate = draft_rate()

    with pytest.raises(
        ValueError,
        match="must change metadata",
    ):
        rate.update_metadata(
            rate.metadata,
            occurred_at=LATER,
        )


@pytest.mark.parametrize(
    "operation",
    [
        lambda rate: rate.update_rate(
            "0.67",
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda rate: rate.update_spread(
            "50",
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda rate: rate.update_provider_reference(
            "fxlock-002",
            occurred_at=NOW - timedelta(seconds=1),
        ),
        lambda rate: rate.update_metadata(
            {"corridor": "AU-CA"},
            occurred_at=NOW - timedelta(seconds=1),
        ),
    ],
)
def test_updates_reject_earlier_timestamp(
    operation: object,
) -> None:
    with pytest.raises(
        ValueError,
        match="must not be earlier",
    ):
        operation(draft_rate())  # type: ignore[operator]


def test_equal_timestamp_is_allowed() -> None:
    rate = draft_rate()

    updated = rate.update_rate(
        "0.67",
        occurred_at=rate.updated_at,
    )

    assert updated.updated_at == rate.updated_at
    assert updated.version == rate.version + 1


def test_multiple_updates_increment_once_each() -> None:
    original = draft_rate()

    first = original.update_rate(
        "0.67",
        occurred_at=LATER,
    )
    second = first.update_spread(
        "50",
        occurred_at=LATER,
    )
    third = second.update_provider_reference(
        "fxlock-002",
        occurred_at=LATER,
    )

    assert original.version == 1
    assert first.version == 2
    assert second.version == 3
    assert third.version == 4


def test_original_rate_remains_unchanged() -> None:
    original = draft_rate()

    updated = original.publish(
        occurred_at=LATER,
    )

    assert original.status is ExchangeRateStatus.DRAFT
    assert original.version == 1
    assert original.updated_at == NOW

    assert updated.status is ExchangeRateStatus.ACTIVE
    assert updated.version == 2


def test_serialization_reflects_lifecycle() -> None:
    published = draft_rate().publish(
        reason="approved",
        occurred_at=LATER,
    )

    payload = published.canonical_dict()

    assert payload["status"] == "active"
    assert payload["version"] == 2
    assert payload["updated_at"] == LATER.isoformat()
    assert payload["metadata"]["lifecycle_action"] == (
        "publish"
    )


def test_exchange_rate_lifecycle_methods_available() -> None:
    methods = (
        "publish",
        "suspend",
        "resume",
        "supersede",
        "expire",
        "revoke",
        "update_rate",
        "update_spread",
        "update_validity",
        "update_provider_reference",
        "update_metadata",
    )

    for method in methods:
        assert callable(getattr(ExchangeRate, method))
