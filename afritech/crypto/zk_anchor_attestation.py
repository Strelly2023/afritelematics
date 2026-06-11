"""Deterministic zero-knowledge style attestations for anchor batches."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from afritech.crypto.anchor_batching import AnchorMerkleBatch
from afritech.zk.interface import ZKProof, ZKProver
from afritech.zk.mock_snark import MockSNARKVerifier


class MockAnchorBatchProver(ZKProver):
    scheme = "mock"

    def prove(
        self,
        input_data: dict[str, Any],
        output_data: dict[str, Any],
    ) -> ZKProof:
        public_inputs = self.build_public_inputs(input_data, output_data)
        proof_bytes = hashlib.sha256(
            json.dumps(public_inputs, sort_keys=True, separators=(",", ":")).encode()
        ).digest()
        return ZKProof(
            proof=proof_bytes,
            public_inputs=public_inputs,
            scheme=self.scheme,
            metadata={"profile": "anchor_batch_consistency"},
        )


@dataclass(frozen=True)
class AnchorBatchZKAttestation:
    batch_id: str
    batch_root: str
    proof_hash: str
    scheme: str
    public_inputs: dict[str, Any]
    verification_status: str
    authority_boundary: str = "zk_attests_public_input_consistency_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "schema": "afritech.anchor_batch_zk_attestation.v1",
            "batch_id": self.batch_id,
            "batch_root": self.batch_root,
            "proof_hash": self.proof_hash,
            "scheme": self.scheme,
            "public_inputs": self.public_inputs,
            "verification_status": self.verification_status,
            "authority_boundary": self.authority_boundary,
        }


def build_anchor_batch_zk_attestation(
    batch: AnchorMerkleBatch,
) -> tuple[AnchorBatchZKAttestation, ZKProof]:
    prover = MockAnchorBatchProver()
    verifier = MockSNARKVerifier()
    input_data = {
        "batch_id": batch.batch_id,
        "anchor_ids": list(batch.anchor_ids),
        "publication_target": batch.publication_target,
    }
    output_data = {
        "batch_root": batch.batch_root,
        "manifest_hash": batch.manifest_hash,
        "batch_size": batch.batch_size,
    }
    proof = prover.prove(input_data, output_data)
    verified = verifier.verify(proof)
    attestation = AnchorBatchZKAttestation(
        batch_id=batch.batch_id,
        batch_root=batch.batch_root,
        proof_hash=proof.proof_hash,
        scheme=proof.scheme,
        public_inputs=proof.public_inputs,
        verification_status="VERIFIED" if verified else "REJECTED",
    )
    return attestation, proof


__all__ = [
    "AnchorBatchZKAttestation",
    "MockAnchorBatchProver",
    "build_anchor_batch_zk_attestation",
]
