from __future__ import annotations

import json
from copy import deepcopy

import pytest

from ecosystems.afriride.geo.types import GeoPoint

from afritech.identity.mobility_participant import MobilityParticipant
from afritech.mobility.trust_dispatch import DispatchCandidate, DispatchRequest, run_trust_aware_dispatch
from afritech.mobility.trust_network import TrustUpdateEvent, build_trust_profile
from afritech.mobility.intelligence_layer import (
    MobilityInsight,
    build_mobility_insight,
    build_mobility_insight_proof,
    export_mobility_insight,
    evaluate_intelligence_invariants,
    validate_mobility_insight,
    validate_intelligence_invariants,
    IntelligenceLayerError,
)


@pytest.fixture
def trust_engine():
    class _TrustEngine:
        def __init__(self) -> None:
            self._scores = {"driver-1": 88.0}
            self._events = 3

        def score(self, participant_id: str) -> float:
            return self._scores[participant_id]

        def event_count(self) -> int:
            return self._events

        def apply_intelligence(self, insight: MobilityInsight) -> None:
            return None

    return _TrustEngine()


def test_intelligence_happy_path():
    insight = build_mobility_insight(
        insight_type="forecast",
        region="melbourne",
        demand=120,
        supply=80,
    )

    assert isinstance(insight, MobilityInsight)
    assert insight.insight_type == "forecast"
    assert insight.confidence_score >= 0.0
    assert insight.confidence_score <= 1.0


def test_invalid_input_rejected():
    with pytest.raises(IntelligenceLayerError):
        build_mobility_insight(
            insight_type="invalid-type",
            region="melbourne",
            demand=-1,
            supply=0,
        )


def test_intelligence_determinism():
    a = build_mobility_insight("forecast", "melbourne", 100, 50)
    b = build_mobility_insight("forecast", "melbourne", 100, 50)

    assert a.canonical_dict() == b.canonical_dict()


def test_intelligence_hash_stability():
    a = build_mobility_insight("forecast", "melbourne", 100, 50)
    b = build_mobility_insight("forecast", "melbourne", 100, 50)

    assert a.insight_hash == b.insight_hash


def test_intelligence_replay_stability():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)

    rebuilt = MobilityInsight.from_mapping(insight.canonical_dict())

    assert insight.canonical_dict() == rebuilt.canonical_dict()


def test_replay_produces_same_hash():
    insight = build_mobility_insight("forecast", "melbourne", 120, 60)
    rebuilt = MobilityInsight.from_mapping(insight.canonical_dict())

    assert insight.insight_hash == rebuilt.insight_hash


def test_intelligence_cannot_override_dispatch():
    insight = build_mobility_insight("forecast", "melbourne", 120, 60)

    assert "dispatch" not in insight.canonical_dict()


def test_intelligence_cannot_override_proof():
    insight = build_mobility_insight("forecast", "melbourne", 120, 60)

    assert "proof" not in insight.canonical_dict()


def test_intelligence_cannot_override_settlement():
    insight = build_mobility_insight("forecast", "melbourne", 120, 60)

    assert "settlement" not in insight.canonical_dict()


def test_intelligence_advisory_only_flag():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)

    assert insight.is_advisory is True


def test_intelligence_does_not_mutate_external_state():
    base_input = {
        "region": "melbourne",
        "demand": 100,
        "supply": 50,
    }

    original = deepcopy(base_input)
    build_mobility_insight("forecast", **base_input)

    assert base_input == original


def test_schema_is_stable():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    data = insight.canonical_dict()

    assert "insight_type" in data
    assert "confidence_score" in data
    assert "insight_hash" in data


def test_serialization_round_trip():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)

    encoded = json.dumps(insight.canonical_dict())
    decoded = json.loads(encoded)

    rebuilt = MobilityInsight.from_mapping(decoded)

    assert insight.canonical_dict() == rebuilt.canonical_dict()


def test_validate_valid_insight():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)

    assert validate_mobility_insight(insight) is True


def test_validate_rejects_tampered_hash():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    tampered = deepcopy(insight.canonical_dict())

    tampered["insight_hash"] = "f" * 64

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(tampered)


def test_tampered_confidence_detected():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    tampered = deepcopy(insight.canonical_dict())

    tampered["confidence_score"] = 0.99

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(tampered)


def test_tampered_recommendation_detected():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    tampered = deepcopy(insight.canonical_dict())

    tampered["recommendation"] = "force driver assignment"

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(tampered)


def test_detects_drift():
    a = build_mobility_insight("forecast", "melbourne", 100, 50)
    b = build_mobility_insight("forecast", "melbourne", 101, 50)

    assert a.insight_hash != b.insight_hash


def test_reproducibility_under_load():
    results = [
        build_mobility_insight("forecast", "melbourne", 100, 50).insight_hash
        for _ in range(20)
    ]

    assert len(set(results)) == 1


def test_export_mobility_insight(tmp_path):
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)

    exported = export_mobility_insight(tmp_path, insight)

    assert exported["json"].exists()
    assert exported["proof"].exists()

    loaded = json.loads(exported["proof"].read_text())

    assert loaded["insight_hash"] == insight.insight_hash


def test_export_is_deterministic(tmp_path):
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)

    first = export_mobility_insight(tmp_path, insight)
    second = export_mobility_insight(tmp_path, insight)

    assert first["proof"].read_text() == second["proof"].read_text()


def test_evidence_link_order_does_not_change_hash():
    a = build_mobility_insight(
        "forecast",
        "melbourne",
        100,
        50,
        evidence_links=["a", "b"],
    )
    b = build_mobility_insight(
        "forecast",
        "melbourne",
        100,
        50,
        evidence_links=["b", "a"],
    )

    assert a.insight_hash == b.insight_hash


def test_metadata_order_does_not_change_hash():
    a = build_mobility_insight(
        "forecast",
        "melbourne",
        100,
        50,
        metadata={"a": 1, "b": 2},
    )
    b = build_mobility_insight(
        "forecast",
        "melbourne",
        100,
        50,
        metadata={"b": 2, "a": 1},
    )

    assert a.insight_hash == b.insight_hash


def test_authority_boundary_tampering_rejected():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    tampered = insight.canonical_dict()
    tampered["authority_boundary"] = "hack"

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(tampered)


def test_source_data_hash_tampering_rejected():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    tampered = insight.canonical_dict()
    tampered["demand"] = 999

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(tampered)


def test_invalid_evidence_links_rejected():
    with pytest.raises(IntelligenceLayerError):
        build_mobility_insight("forecast", "melbourne", 100, 50, evidence_links=[None])


def test_export_integrity(tmp_path):
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    exported = export_mobility_insight(tmp_path, insight)

    proof = json.loads(exported["proof"].read_text())

    assert proof["insight_hash"] == insight.insight_hash
    assert proof["verified"] is True


def test_proof_hash_tampering_rejected(tmp_path):
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    exported = export_mobility_insight(tmp_path, insight)

    proof = json.loads(exported["proof"].read_text())
    proof["insight_hash"] = "f" * 64

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(proof)


def test_proof_authority_boundary_tampering_rejected(tmp_path):
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    exported = export_mobility_insight(tmp_path, insight)

    proof = json.loads(exported["proof"].read_text())
    proof["authority_boundary"] = "fake-boundary"

    with pytest.raises(IntelligenceLayerError):
        validate_mobility_insight(proof)


def test_large_scale_replay_stability():
    hashes = set()

    for _ in range(1000):
        metadata = {"a": 1, "b": 2}
        items = ["x", "y", "z"]
        items.reverse()

        insight = build_mobility_insight(
            "forecast",
            "melbourne",
            100,
            50,
            evidence_links=items,
            metadata=metadata,
        )
        hashes.add(insight.insight_hash)

    assert len(hashes) == 1


def test_invariant_compliance():
    insight = build_mobility_insight("forecast", "melbourne", 100, 50)
    proof = build_mobility_insight_proof(insight)
    report = evaluate_intelligence_invariants(insight, proof)

    assert report.verified is True
    assert validate_intelligence_invariants(report) is True


def _dispatch_request() -> DispatchRequest:
    return DispatchRequest.from_mapping(
        {
            "operation_id": "dispatch-001",
            "operation_type": "ride",
            "origin": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "destination": {"lat": -37.8036, "lon": 144.9731, "timestamp": 1_700_000_500},
            "constraints": {"required_roles": ["driver"]},
            "timestamp": 1_700_000_000,
        }
    )


def _dispatch_candidate() -> DispatchCandidate:
    participant = MobilityParticipant.from_mapping(
        {
            "participant_id": "driver-001",
            "display_name": "Driver One",
            "roles": ["driver"],
            "verification_status": "verified",
            "trust_score": 92.0,
            "evidence_links": ["driver-001-ev"],
            "metadata": {},
        }
    )
    return DispatchCandidate.from_mapping(
        {
            "participant": participant.canonical_dict(),
            "location": {"lat": -37.8136, "lon": 144.9631, "timestamp": 1_700_000_000},
            "availability": True,
            "reliability_score": 95.0,
            "anomaly_rate": 0.0,
            "supported_operations": ["ride"],
            "capacity": 1,
            "metadata": {},
        }
    )


def test_intelligence_does_not_override_dispatch():
    insight = build_mobility_insight("forecast", "melbourne", 200, 50)
    request = _dispatch_request()
    candidate = _dispatch_candidate()

    dispatch_before = run_trust_aware_dispatch(request, (candidate,))
    dispatch_after = run_trust_aware_dispatch(request, (candidate,))

    assert dispatch_before.canonical_dict() == dispatch_after.canonical_dict()
    assert insight.is_advisory is True


def test_intelligence_does_not_override_trust():
    insight = build_mobility_insight("forecast", "melbourne", 200, 50)
    event = TrustUpdateEvent.from_mapping(
        {
            "event_id": "event-001",
            "participant_id": "driver-001",
            "event_type": "successful_delivery",
            "source_operation_id": "operation-001",
            "dispatch_hash": "a" * 64,
            "custody_hash": "b" * 64,
            "settlement_hash": "c" * 64,
            "evidence_link": "event-001-ev",
            "timestamp": 1_700_000_000,
            "rating": 5.0,
            "verified": True,
            "metadata": {},
        }
    )
    profile_before = build_trust_profile("driver-001", (event,))
    profile_after = build_trust_profile("driver-001", (event,))

    assert profile_before.canonical_dict() == profile_after.canonical_dict()
    assert insight.recommendation in {"monitor_demand_balance", "monitor_supply_balance"}


def test_intelligence_guides_but_does_not_mutate():
    insight = build_mobility_insight("forecast", "melbourne", 200, 50)

    assert "increase" not in insight.canonical_dict()["recommendation"]
    assert insight.is_advisory is True


def test_intelligence_cannot_modify_trust_score(trust_engine):
    insight = build_mobility_insight("forecast", "melbourne", 200, 50)

    before = trust_engine.score("driver-1")
    trust_engine.apply_intelligence(insight)
    after = trust_engine.score("driver-1")

    assert before == after


def test_intelligence_cannot_create_trust_event(trust_engine):
    insight = build_mobility_insight("forecast", "melbourne", 200, 50)

    events_before = trust_engine.event_count()
    trust_engine.apply_intelligence(insight)
    events_after = trust_engine.event_count()

    assert events_before == events_after
