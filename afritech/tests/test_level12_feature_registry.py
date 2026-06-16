from __future__ import annotations

from afritech.evidence.evidence_index import (
    build_evidence_index,
    replay_events_from_feature_candidates,
)
from afritech.feature_registry.derivation import derive_features
from afritech.features import (
    EVIDENCE_INDEX,
    FEATURE_CANDIDATES,
    FEATURES,
    registry_payload,
)
from afritech.registry.snapshot import generate_snapshot, verify_snapshot


def test_replay_native_evidence_index_carries_origin_events():
    events = replay_events_from_feature_candidates(FEATURE_CANDIDATES)
    index = build_evidence_index(events)

    assert index
    assert set(index) == set(EVIDENCE_INDEX)
    assert {
        path: artifact.hash
        for path, artifact in index.items()
    } == {
        path: artifact.hash
        for path, artifact in EVIDENCE_INDEX.items()
    }
    assert all(artifact.origin_event.startswith("feature-evidence:") for artifact in index.values())
    assert all(artifact.timestamp.endswith("Z") for artifact in index.values())


def test_feature_projection_engine_exports_only_provable_features():
    derived = derive_features(FEATURE_CANDIDATES, EVIDENCE_INDEX)

    assert derived == FEATURES
    assert all(feature.evidence for feature in derived)


def test_signed_snapshot_verifies_external_identity():
    snapshot = generate_snapshot("v1")
    result = verify_snapshot(snapshot)

    assert snapshot["signed"] is True
    assert snapshot["signature"]["algorithm"] == "Ed25519"
    assert result["verified"] is True
    assert result["production_ready_feature_count"] == 3


def test_registry_payload_exposes_level12_guarantees():
    payload = registry_payload()

    assert payload["generation_mode"] == "REPLAY_DERIVED_EVIDENCE_PROJECTION"
    assert payload["signature"]["algorithm"] == "Ed25519"
    assert payload["production_ready_feature_count"] == 3
    assert payload["verified_true"] is True
    assert payload["production_proven"] is False
