from __future__ import annotations

from afritech.crypto.anchor_batching import build_anchor_merkle_batch
from afritech.crypto.anchor_publication import build_anchor_publication_envelope
from afritech.crypto.external_anchor import build_external_anchor_commitment
from afritech.crypto.zk_anchor_attestation import build_anchor_batch_zk_attestation


def _batch():
    commitment = build_external_anchor_commitment(
        tenant_id="tenant-core",
        region_id="mel-ap-southeast-2",
        trace_hash="a" * 64,
        replay_hash="b" * 64,
        receipt_hash="c" * 64,
        authority_hash="d" * 64,
        execution_fingerprint="e" * 64,
    )
    envelope = build_anchor_publication_envelope(
        commitment,
        publication_target="public-ledger-test-anchor",
        external_reference="ledger-ref-zk-001",
    )
    return build_anchor_merkle_batch(
        (envelope,),
        publication_target="public-ledger-test-anchor",
    )


def test_anchor_batch_zk_attestation_verifies_consistency() -> None:
    attestation, proof = build_anchor_batch_zk_attestation(_batch())

    assert attestation.verification_status == "VERIFIED"
    assert attestation.scheme == "mock"
    assert attestation.proof_hash == proof.proof_hash
    assert attestation.public_inputs["input_hash"]
    assert attestation.public_inputs["output_hash"]
