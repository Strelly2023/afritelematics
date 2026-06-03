from afritech.crypto.merkle import compute_merkle_root
from afritech.crypto.signature import sign_data
from afritech.services.cross_proof_verifier import verify_cross_system_proof


def load_sample_proof():
    logs = [
        {"event": "source_committed", "system": "afriride", "sequence": 1},
        {"event": "target_verified", "system": "afritech", "sequence": 2},
    ]
    merkle_root = compute_merkle_root(logs)
    return {
        "version": "v1",
        "system_id": "afriride",
        "network": "test",
        "timestamp": "2026-05-28T00:00:00Z",
        "proof_type": "cross_system_proof",
        "data": {"logs": logs},
        "merkle_root": merkle_root,
        "hash_algorithm": "sha256",
        "signature": sign_data(merkle_root),
        "public_key_id": "afritech-key-01",
    }


def test_valid_cross_proof():
    proof = load_sample_proof()
    assert verify_cross_system_proof(proof) is True
