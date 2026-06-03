from __future__ import annotations

import pytest

from afritech.ci.marketplace_simulation_validator import (
    run_marketplace_simulation_validation,
)
from ecosystems.afriride.simulation.marketplace_proof import (
    AUTHORITY_DISCLAIMER,
    REQUIRED_REJECTIONS,
    REQUIRED_SCENARIOS,
    MarketplaceProofError,
    _normalize_market_event,
    run_marketplace_proof,
)


def test_marketplace_proof_covers_required_scenarios():
    report = run_marketplace_proof()

    assert tuple(scenario.scenario_name for scenario in report.scenarios) == REQUIRED_SCENARIOS
    assert report.verified is True
    assert report.authority_disclaimer == AUTHORITY_DISCLAIMER


def test_marketplace_proof_preserves_partition_and_replay_hashes():
    report = run_marketplace_proof()

    assert len(report.market_replay_hash) == 64
    assert len(report.partition_order_hash) == 64
    assert all(len(scenario.replay_hash) == 64 for scenario in report.scenarios)
    assert all(len(scenario.partition_order_hash) == 64 for scenario in report.scenarios)


def test_marketplace_proof_rejects_authority_cases():
    report = run_marketplace_proof()

    assert report.rejected_authority_cases == REQUIRED_REJECTIONS


def test_marketplace_rejects_client_side_surge_authority():
    with pytest.raises(MarketplaceProofError, match="client_side_surge"):
        _normalize_market_event(
            {"client_side_surge": "3.0", "ride_id": "ride.test"},
            event_type="surge",
        )


def test_marketplace_proof_hash_is_deterministic():
    first = run_marketplace_proof()
    second = run_marketplace_proof()

    assert first.report_hash() == second.report_hash()


def test_marketplace_simulation_validator_report_is_verified():
    report = run_marketplace_simulation_validation()

    assert report.verified is True
    assert report.scenario_count == len(REQUIRED_SCENARIOS)
    assert report.rejected_authority_cases == REQUIRED_REJECTIONS
    assert len(report.report_hash()) == 64

