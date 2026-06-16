from __future__ import annotations

import json
from pathlib import Path

import pytest

from afritech.features import (
    EVIDENCE_INDEX,
    FEATURES,
    FEATURE_CANDIDATES,
    REGISTRY_CLASSIFICATION,
    REGISTRY_GENERATION_MODE,
    REGISTRY_STATUS,
    SYSTEM_STATUS,
    boundary_guard_exists,
    boundary_guard_valid,
    derive_features_from_evidence,
    evidence_complete,
    evidence_hash,
    evidence_chain_hash,
    feature_hash,
    feature_by_id,
    feature_ids,
    feature_matrix,
    feature_names,
    file_non_empty,
    generate_claim_snapshot,
    incomplete_features,
    path_exists,
    registry_payload,
    scan_repository_for_evidence,
    status_summary,
    valid_json_file,
    valid_proof_payload,
)


ROOT = Path(__file__).resolve().parents[2]


def test_feature_catalog_keeps_existing_canonical_names():
    assert feature_names() == [
        "Trust Kernel",
        "AfriTPPS Execution",
        "Cross-Domain Orchestration",
        "Federation",
        "Resilience Hardening",
        "AfriPower Intelligence",
        "Governance Chain",
        "Classification CI",
        "Pilot Gates",
        "Driver Identity Proof",
        "Trip Integrity Proof",
        "Payment Proof Anchor",
        "Domain Surfaces",
        "Legal Evidence Export",
        "Operational Tooling",
    ]


def test_feature_lookup_success():
    feature = feature_by_id("trust-kernel")

    assert feature.id == "trust-kernel"
    assert feature.feature_id == "trust-kernel"
    assert feature.name == "Trust Kernel"


def test_all_features_have_unique_ids():
    ids = [feature.id for feature in FEATURES]

    assert len(ids) == len(set(ids))
    assert ids == feature_ids()
    assert ids[0] == "trust-kernel"
    assert ids[-1] == "operational-tooling"
    assert len(FEATURES) == len(FEATURE_CANDIDATES)


def test_features_are_derived_from_repository_evidence_index():
    evidence_index = scan_repository_for_evidence(FEATURE_CANDIDATES)
    derived = derive_features_from_evidence(evidence_index, FEATURE_CANDIDATES)

    assert evidence_index == EVIDENCE_INDEX
    assert derived == FEATURES
    assert all(feature in derived for feature in FEATURE_CANDIDATES)


def test_unprovable_candidate_does_not_exist_in_derived_registry():
    broken = FEATURE_CANDIDATES[0]
    filtered_index = {
        path: artifact
        for path, artifact in EVIDENCE_INDEX.items()
        if path != broken.evidence[0].path
    }

    derived = derive_features_from_evidence(filtered_index, FEATURE_CANDIDATES)

    assert broken not in derived
    assert all(feature.id != broken.id for feature in derived)


def test_feature_dependencies_are_satisfied_by_derived_registry_order():
    completed = set()

    for feature in FEATURES:
        assert set(feature.dependencies).issubset(completed), feature.id
        completed.add(feature.id)


def test_all_features_have_versions():
    for feature in FEATURES:
        assert feature.version.startswith("v")
        assert feature.last_updated


def test_all_required_evidence_paths_exist():
    for feature in FEATURES:
        for evidence_ref in feature.evidence:
            if evidence_ref.required:
                assert path_exists(evidence_ref), (
                    f"Missing evidence: {feature.id} -> {evidence_ref.path}"
                )


def test_all_required_evidence_is_non_empty():
    for feature in FEATURES:
        for evidence_ref in feature.evidence:
            if evidence_ref.required:
                assert file_non_empty(evidence_ref), (
                    f"Empty evidence: {feature.id} -> {evidence_ref.path}"
                )


def test_json_evidence_is_valid_json():
    for feature in FEATURES:
        for evidence_ref in feature.evidence:
            assert valid_json_file(evidence_ref), (
                f"Invalid JSON: {feature.id} -> {evidence_ref.path}"
            )


def test_proof_evidence_has_required_keys():
    for feature in FEATURES:
        for evidence_ref in feature.evidence:
            assert valid_proof_payload(evidence_ref), (
                f"Invalid proof payload: {feature.id} -> {evidence_ref.path}"
            )


def test_all_features_have_boundary_guards():
    for feature in FEATURES:
        assert feature.boundary_guard
        assert boundary_guard_exists(feature)
        assert boundary_guard_valid(feature)


def test_only_verification_products_are_production_ready_without_authorization():
    production_ready = [
        feature.id for feature in FEATURES if feature.activation_status == "PRODUCTION_READY"
    ]

    assert production_ready == [
        "driver-identity-proof",
        "trip-integrity-proof",
        "payment-proof-anchor",
    ]

    assert SYSTEM_STATUS["live_pilot_authorized"] is False
    assert SYSTEM_STATUS["production_proven"] is False
    assert SYSTEM_STATUS["economic_activation_allowed"] is False


def test_all_features_are_evidence_complete():
    assert incomplete_features() == []

    for feature in FEATURES:
        assert evidence_complete(feature), feature.id
        assert evidence_chain_hash(feature)


def test_all_evidence_kinds_present():
    required_kinds = {"implementation", "test", "replay", "proof"}

    for feature in FEATURES:
        kinds = {evidence_ref.kind for evidence_ref in feature.evidence}
        assert required_kinds.issubset(kinds), feature.id


def test_boundary_matches_guard():
    for feature in FEATURES:
        assert feature.boundary_guard.endswith(".py")
        assert any(
            evidence_ref.kind == "boundary_guard"
            and evidence_ref.path == feature.boundary_guard
            for evidence_ref in feature.evidence
        )


def test_feature_matrix_is_serializable_and_boundary_aware():
    matrix = feature_matrix()

    assert len(matrix) == len(FEATURES)
    assert matrix[0]["id"] == "trust-kernel"
    assert matrix[0]["feature_id"] == "trust-kernel"
    assert all(row["boundary"] for row in matrix)
    assert all(row["boundary_guard"] for row in matrix)
    assert all(row["evidence_complete"] is True for row in matrix)
    assert all(
        row["technical_status"] in {"IMPLEMENTED", "PARTIAL", "PLANNED"}
        for row in matrix
    )
    assert all(
        row["activation_status"]
        in {"GATED", "CONTROLLED_PILOT_READY", "PRODUCTION_READY"}
        for row in matrix
    )


def test_registry_payload_exposes_level_11_classification_without_activation():
    payload = registry_payload()

    assert payload["classification"] == REGISTRY_CLASSIFICATION
    assert payload["classification"] == "GOVERNED_EVIDENCE_VALIDATED_FEATURE_REGISTRY"
    assert payload["status"] == REGISTRY_STATUS
    assert payload["status"] == "FEATURE_REGISTRY_LEVEL_12"
    assert payload["generation_mode"] == REGISTRY_GENERATION_MODE
    assert payload["generation_mode"] == "REPLAY_DERIVED_EVIDENCE_PROJECTION"
    assert payload["read_only"] is True
    assert payload["creates_authority"] is False
    assert payload["candidate_feature_count"] == len(FEATURE_CANDIDATES)
    assert payload["feature_count"] == len(FEATURES)
    assert payload["complete_feature_count"] == len(FEATURES)
    assert payload["feature_hash"] == feature_hash()
    assert payload["evidence_hash"] == evidence_hash()
    assert payload["registry_hash"]
    assert payload["signature"]["algorithm"] == "Ed25519"
    assert payload["signature"]["scope"] == "registry_payload"
    assert payload["signature"]["public_key"]
    assert payload["signature"]["value"]
    assert payload["production_ready_feature_count"] == 3
    assert payload["production_ready_feature_ids"] == [
        "driver-identity-proof",
        "trip-integrity-proof",
        "payment-proof-anchor",
    ]
    assert payload["verified_true_threshold"] == 3
    assert payload["verified_true"] is True
    assert payload["live_pilot_authorized"] is False
    assert payload["production_proven"] is False
    assert payload["economic_activation_allowed"] is False
    assert payload["claim_history"] == "docs/governance/AFRITECH_FEATURE_CLAIM_HISTORY.md"


def test_claim_snapshot_is_machine_verifiable():
    snapshot = generate_claim_snapshot("v1")

    assert snapshot["schema"] == "afritech.feature_registry_snapshot.v1"
    assert snapshot["version"] == "v1"
    assert snapshot["classification"] == REGISTRY_CLASSIFICATION
    assert snapshot["status"] == REGISTRY_STATUS
    assert snapshot["feature_hash"] == feature_hash()
    assert snapshot["evidence_hash"] == evidence_hash()
    assert snapshot["registry_hash"] == registry_payload()["registry_hash"]
    assert snapshot["snapshot_hash"]
    assert snapshot["production_ready_feature_count"] == 3


def test_persisted_claim_snapshot_exists_and_matches_current_registry_identity():
    snapshot_path = ROOT / "reports/feature_registry_history/v1.json"

    assert snapshot_path.exists()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert snapshot["schema"] == "afritech.feature_registry_snapshot.v1"
    assert snapshot["classification"] == REGISTRY_CLASSIFICATION
    assert snapshot["status"] == REGISTRY_STATUS
    assert snapshot["feature_count"] == len(FEATURES)
    assert snapshot["candidate_feature_count"] == len(FEATURE_CANDIDATES)
    assert snapshot["production_ready_feature_count"] == 3
    assert snapshot["signature"]["algorithm"] == "Ed25519"
    assert snapshot["signature"]["public_key"]


def test_status_summary_preserves_activation_boundaries():
    assert "live_pilot_authorized=False" in status_summary()
    assert "production_proven=False" in status_summary()


def test_unknown_feature_lookup_fails_closed():
    with pytest.raises(KeyError):
        feature_by_id("missing-feature")
