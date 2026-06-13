from __future__ import annotations

import pytest

from afritech.ci import afripay_concurrency_validator as validator


@pytest.mark.django_db(transaction=True)
def test_afripay_concurrency_validator_passes():
    report = validator.validate()

    assert report.verified is True
    assert report.idempotency_winners == 1
    assert report.treasury_successes == validator.TREASURY_WORKERS
    assert len(set(report.webhook_event_ids)) == 1
    assert len(set(report.flutterwave_references)) == 1
    assert len(set(report.mpesa_references)) == 1


@pytest.mark.django_db(transaction=True)
def test_idempotency_race_has_single_winner():
    assert validator._idempotency_race() == 1


@pytest.mark.django_db(transaction=True)
def test_treasury_race_fully_reserves_pool():
    assert validator._treasury_race() == validator.TREASURY_WORKERS


@pytest.mark.django_db(transaction=True)
def test_duplicate_webhook_storm_collapses_to_single_event():
    event_ids = validator._duplicate_webhook_storm()

    assert len(set(event_ids)) == 1


@pytest.mark.django_db(transaction=True)
def test_provider_retry_storm_is_deterministic():
    flutterwave_refs, mpesa_refs = validator._provider_retry_storm()

    assert len(set(flutterwave_refs)) == 1
    assert len(set(mpesa_refs)) == 1
