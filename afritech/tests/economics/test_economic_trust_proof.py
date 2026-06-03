from __future__ import annotations

from decimal import Decimal

import pytest

from afritech.ci.economic_trust_validator import run_economic_trust_validation
from afritech.payments.economic_trust_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_PROOFS,
    REQUIRED_REJECTIONS,
    EconomicTrustProofError,
    FarePlan,
    _normalize_economic_payload,
    run_economic_trust_proof,
)


def test_economic_trust_proof_covers_required_proofs():
    report = run_economic_trust_proof()

    assert report.proof_names == REQUIRED_PROOFS
    assert report.verified is True
    assert report.authority_disclaimer == AUTHORITY_DISCLAIMER


def test_deterministic_fare_calculation_hash_is_stable():
    first = FarePlan(
        ride_id="ride.test",
        distance_km=Decimal("12.40"),
        duration_minutes=Decimal("28.00"),
        base_fare=Decimal("4.20"),
        per_km_rate=Decimal("1.70"),
        per_minute_rate=Decimal("0.45"),
    )
    second = FarePlan(
        ride_id="ride.test",
        distance_km=Decimal("12.40"),
        duration_minutes=Decimal("28.00"),
        base_fare=Decimal("4.20"),
        per_km_rate=Decimal("1.70"),
        per_minute_rate=Decimal("0.45"),
    )

    assert first.total_fare == Decimal("37.88")
    assert first.fare_hash() == second.fare_hash()


def test_economic_trust_proof_rejects_authority_cases():
    report = run_economic_trust_proof()

    assert report.rejected_cases == REQUIRED_REJECTIONS


def test_economic_payload_rejects_provider_fare_authority():
    with pytest.raises(EconomicTrustProofError, match="authoritative_fare"):
        _normalize_economic_payload(
            {"authoritative_fare": "1.00", "provider_status": "paid"}
        )


def test_economic_trust_report_hash_is_deterministic():
    first = run_economic_trust_proof()
    second = run_economic_trust_proof()

    assert first.report_hash() == second.report_hash()
    assert len(first.economic_replay_hash) == 64


def test_economic_trust_validator_report_is_verified():
    report = run_economic_trust_validation()

    assert report.verified is True
    assert report.proof_names == REQUIRED_PROOFS
    assert report.rejected_cases == REQUIRED_REJECTIONS
    assert len(report.report_hash()) == 64
