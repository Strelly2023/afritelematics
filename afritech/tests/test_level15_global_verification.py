from __future__ import annotations

from afritech.global_verification import (
    build_global_verification_bundle,
    verify_global_verification_bundle,
)


def test_level15_global_verification_bundle_is_independently_verifiable():
    bundle = build_global_verification_bundle()
    verification = verify_global_verification_bundle(bundle)

    assert bundle.classification == "LEVEL_15_GLOBAL_PUBLIC_VERIFICATION_LAYER"
    assert bundle.level == "LEVEL_15"
    assert bundle.status == "GLOBAL_PUBLIC_VERIFICATION_READY"
    assert verification["verified"] is True
    assert verification["bundle_hash_valid"] is True
    assert verification["cross_network"]["network_count"] >= 3
    assert verification["cross_network"]["optional_onchain_anchor_present"] is True
    assert verification["guarantees"]["truth_independent_of_origin_system"] is True
    assert verification["guarantees"]["optional_onchain_anchoring_supported"] is True
    assert verification["guarantees"]["no_production_state_can_be_falsely_implied"] is True


def test_level15_global_verification_rejects_tampered_anchor():
    payload = build_global_verification_bundle().canonical_dict()
    payload["cross_network_anchors"][0]["receipt"]["proof_hash"] = "tampered"

    verification = verify_global_verification_bundle(payload)

    assert verification["verified"] is False
    assert verification["cross_network"]["valid_anchor_count"] == 2
    assert verification["cross_network"]["anchor_hash_valid"] is False


def test_level15_global_verification_rejects_tampered_registry_export():
    payload = build_global_verification_bundle().canonical_dict()
    payload["registry"]["features"] = []

    verification = verify_global_verification_bundle(payload)

    assert verification["verified"] is False
    assert verification["registry"]["verified"] is False
    assert verification["bundle_hash_valid"] is False
