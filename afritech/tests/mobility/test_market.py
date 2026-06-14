from __future__ import annotations

import json
from decimal import Decimal
from copy import deepcopy

import pytest

from afritech.mobility.federation import FederatedParticipant
from afritech.mobility.market import (
    AUTHORITY_BOUNDARY,
    ALLOWED_INCENTIVES,
    MarketAllocation,
    MarketGovernanceError,
    MarketState,
    build_market_decision,
    build_market_decision_proof,
    compute_market_decision,
    evaluate_market_invariants,
    export_market_decision_proof,
    validate_market_decision,
    validate_market_invariants,
)
from afritech.mobility.trust_network import TrustUpdateEvent, build_trust_profile


def _trust_profile(participant_id: str, score_hint: float):
    events = (
        TrustUpdateEvent.from_mapping(
            {
                "event_id": f"{participant_id}-event-001",
                "participant_id": participant_id,
                "event_type": "successful_delivery",
                "source_operation_id": "op-001",
                "dispatch_hash": "a" * 64,
                "custody_hash": "b" * 64,
                "settlement_hash": "c" * 64,
                "evidence_link": f"ev-{participant_id}-001",
                "timestamp": 1_700_000_000,
                "rating": 5.0,
                "verified": True,
            }
        ),
    )
    profile = build_trust_profile(participant_id, events)
    return profile


def _participant(participant_id: str, home_network: str, trust_score: float, *, federation_weight: float = 0.85):
    profile = _trust_profile(participant_id, trust_score)
    return FederatedParticipant.from_mapping(
        {
            "participant_id": participant_id,
            "home_network": home_network,
            "roles": ["driver"],
            "trust_profile": profile,
            "federation_status": "verified",
            "federation_weight": federation_weight,
            "verification_level": "verified",
            "cross_network_events": 1,
            "evidence_links": [f"fed-{participant_id}-001"],
            "metadata": {},
        }
    )


def _allocation(participant_id: str, region_id: str, count: int, ts: int) -> MarketAllocation:
    return MarketAllocation.from_mapping(
        {
            "allocation_id": f"{participant_id}-{ts}",
            "participant_id": participant_id,
            "region_id": region_id,
            "assignment_count": count,
            "timestamp": ts,
            "evidence_link": f"alloc-{participant_id}-{ts}",
            "verified": True,
            "metadata": {},
        }
    )


def _state(
    *,
    demand: int = 120,
    supply: int = 80,
    price_hint: float = 1.0,
    allocations: tuple[MarketAllocation, ...] | None = None,
):
    participants = (
        _participant("driver-a", "network-a", 95.0, federation_weight=0.85),
        _participant("driver-b", "network-b", 90.0, federation_weight=0.82),
        _participant("driver-c", "network-c", 85.0, federation_weight=0.80),
    )
    return MarketState.from_mapping(
        {
            "market_id": "market-001",
            "region_id": "melbourne",
            "demand": demand,
            "supply": supply,
            "base_price": "10.00",
            "currency": "AUD",
            "participants": [participant.canonical_dict() for participant in participants],
            "allocation_history": [
                allocation.canonical_dict()
                for allocation in (
                    allocations
                    if allocations is not None
                    else (
                        _allocation("driver-a", "melbourne", 10, 1_700_000_000),
                        _allocation("driver-b", "melbourne", 4, 1_700_000_100),
                        _allocation("driver-c", "melbourne", 2, 1_700_000_200),
                    )
                )
            ],
            "active_incentives": [],
            "timestamp": 1_700_000_500,
            "price_multiplier_hint": price_hint,
            "price_floor": 0.75,
            "price_ceiling": 2.5,
            "max_allocation_share": 0.35,
        }
    )


def test_pricing_determinism():
    state = _state()

    a = build_market_decision(state)
    b = compute_market_decision(state)

    assert a.canonical_dict() == b.canonical_dict()
    assert a.decision_hash == b.decision_hash


def test_supply_demand_balance():
    state = _state(demand=140, supply=60)
    decision = build_market_decision(state)

    assert decision.price_multiplier > 1.0
    assert "driver_bonus_20%" in decision.incentive_plan
    assert dict(decision.fairness_metrics)["supply_demand_balanced"] is True


def test_incentive_application():
    state = _state(demand=160, supply=60)
    decision = build_market_decision(state)

    assert set(decision.incentive_plan).issubset(set(ALLOWED_INCENTIVES))
    assert any(item.startswith("driver_bonus_") for item in decision.incentive_plan)


def test_no_monopoly_allocation():
    state = _state(
        allocations=(
            _allocation("driver-a", "melbourne", 30, 1_700_000_000),
            _allocation("driver-b", "melbourne", 4, 1_700_000_100),
            _allocation("driver-c", "melbourne", 2, 1_700_000_200),
        )
    )
    decision = build_market_decision(state)

    assert dict(decision.fairness_metrics)["rebalance_required"] is True
    assert decision.bias_for("driver-a") < decision.bias_for("driver-b")


def test_balanced_dispatch_distribution():
    state = _state(
        allocations=(
            _allocation("driver-a", "melbourne", 5, 1_700_000_000),
            _allocation("driver-b", "melbourne", 5, 1_700_000_100),
            _allocation("driver-c", "melbourne", 5, 1_700_000_200),
        )
    )
    decision = build_market_decision(state)
    bias_values = [bias for _, bias in decision.dispatch_bias]

    assert round(sum(bias_values), 6) == 1.0
    assert max(bias_values) - min(bias_values) < 0.15


def test_price_changes_on_input_change():
    state_a = _state(demand=120, supply=80)
    state_b = _state(demand=150, supply=80)

    decision_a = build_market_decision(state_a)
    decision_b = build_market_decision(state_b)

    assert decision_a.decision_hash != decision_b.decision_hash
    assert decision_a.adjusted_price != decision_b.adjusted_price


def test_invalid_market_state_rejected():
    with pytest.raises(MarketGovernanceError):
        _state(demand=-1, supply=80)


def test_market_not_authority():
    state = _state()
    decision = build_market_decision(state)

    assert state.authority_boundary == AUTHORITY_BOUNDARY
    assert decision.authority_boundary == AUTHORITY_BOUNDARY
    assert decision.verified is True


def test_market_replay_stability():
    state = _state()

    a = build_market_decision(state)
    b = build_market_decision(state)

    assert a.canonical_dict() == b.canonical_dict()
    assert a.decision_hash == b.decision_hash


def test_fake_demand_spike():
    baseline = build_market_decision(_state(demand=120, supply=80))
    spike = build_market_decision(_state(demand=220, supply=80))

    assert spike.price_multiplier > baseline.price_multiplier
    assert spike.adjusted_price > baseline.adjusted_price


def test_supply_manipulation():
    baseline = build_market_decision(_state(demand=120, supply=100))
    manipulated = build_market_decision(_state(demand=120, supply=40))

    assert manipulated.price_multiplier > baseline.price_multiplier


def test_incentive_abuse_detected():
    state = _state()
    decision = build_market_decision(state)
    tampered = deepcopy(decision.canonical_dict())
    tampered["incentive_plan"].append("unsupported_incentive")

    with pytest.raises(MarketGovernanceError):
        validate_market_decision(state, tampered)


def test_market_invariant_compliance():
    state = _state()
    decision = build_market_decision(state)
    report = evaluate_market_invariants(state, decision)

    assert report.verified is True
    assert validate_market_invariants(report) is True


def test_market_proof_artifact_roundtrip(tmp_path):
    state = _state()
    decision = build_market_decision(state)
    proof = build_market_decision_proof(state, decision)
    exported = export_market_decision_proof(state, tmp_path, decision)

    assert proof["verified"] is True
    assert proof["schema"] == "afritech.mobility.market_decision_proof.v1"
    assert exported["json"].exists()
    assert exported["proof"].exists()


def test_market_serialization_roundtrip():
    state = _state()
    decision = build_market_decision(state)
    decoded = json.loads(json.dumps(decision.canonical_dict(), sort_keys=True))

    assert decoded["decision_hash"] == decision.decision_hash
    assert decoded["adjusted_price"] == format(decision.adjusted_price.quantize(Decimal("0.01")), "f")


def test_market_validator_rejects_tampered_hash():
    state = _state()
    decision = build_market_decision(state)
    tampered = deepcopy(decision.canonical_dict())
    tampered["decision_hash"] = "f" * 64

    with pytest.raises(MarketGovernanceError):
        validate_market_decision(state, tampered)
