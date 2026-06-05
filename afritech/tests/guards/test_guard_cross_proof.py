from __future__ import annotations

from afritech.guards.guard_cross_proof import (
    guard_validate_merkle,
    guard_validate_proof_structure,
    guard_validate_signature,
)


def test_guard_validate_proof_structure_accepts_required_shape():
    proof = {
        "merkle_root": "root",
        "signature": "sig",
        "public_key_id": "key-1",
        "data": {"logs": []},
    }

    assert guard_validate_proof_structure(proof) is True


def test_guard_validate_proof_structure_rejects_missing_logs():
    proof = {
        "merkle_root": "root",
        "signature": "sig",
        "public_key_id": "key-1",
        "data": {},
    }

    assert guard_validate_proof_structure(proof) is False


def test_guard_validate_merkle_rejects_mismatch():
    proof = {"merkle_root": "expected"}

    assert guard_validate_merkle(proof, "observed") is False


def test_guard_validate_signature_rejects_false_result():
    assert guard_validate_signature(False) is False
