"""Per-transaction Merkle inclusion and zero-knowledge style proofs for AfriPay."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Sequence

from afritech.audit.merkle import MerkleTree
from afritech.zk.interface import ZKProof, ZKProver
from afritech.zk.mock_snark import MockSNARKVerifier


PROOF_AUTHORITY_BOUNDARY = "proofs_only_do_not_define_financial_truth"
ZK_AUTHORITY_BOUNDARY = "zk_attests_public_input_consistency_only"


@dataclass(frozen=True)
class TransactionMerkleInclusionProof:
    reference: str
    transaction_report_hash: str
    index: int
    merkle_root: str
    proof_steps: tuple[tuple[str, str], ...]
    authority_boundary: str = PROOF_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return MerkleTree.verify_proof(
            self.transaction_report_hash,
            _proof_as_dicts(self.proof_steps),
            self.merkle_root,
        )

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "index": self.index,
            "merkle_root": self.merkle_root,
            "proof_steps": [
                {"hash": sibling_hash, "position": position}
                for position, sibling_hash in self.proof_steps
            ],
            "reference": self.reference,
            "schema": "afritech.afripay.transaction_merkle_inclusion_proof.v1",
            "transaction_report_hash": self.transaction_report_hash,
            "verified": self.verified,
        }


@dataclass(frozen=True)
class TransactionZKAttestation:
    reference: str
    proof: ZKProof
    verification_status: str
    authority_boundary: str = ZK_AUTHORITY_BOUNDARY

    @property
    def verified(self) -> bool:
        return self.verification_status == "VERIFIED" and MockSNARKVerifier().verify(self.proof)

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "proof": self.proof.to_dict(),
            "proof_hash": self.proof.proof_hash,
            "reference": self.reference,
            "schema": "afritech.afripay.transaction_zk_attestation.v1",
            "verification_status": self.verification_status,
            "verified": self.verified,
        }


class AfriPayTransactionZKProver(ZKProver):
    scheme = "mock"

    def prove(self, input_data: dict[str, Any], output_data: dict[str, Any]) -> ZKProof:
        public_inputs = {
            "input_hash": self._canonical_hash(input_data),
            "output_hash": self._canonical_hash(output_data),
        }
        proof_bytes = sha256(
            json.dumps(public_inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).digest()
        return ZKProof(
            proof=proof_bytes,
            public_inputs=public_inputs,
            scheme=self.scheme,
            metadata={"authority_boundary": ZK_AUTHORITY_BOUNDARY},
        )


def build_transaction_inclusion_proofs(
    transaction_reports: Sequence[Any],
) -> tuple[TransactionMerkleInclusionProof, ...]:
    if not transaction_reports:
        return tuple()

    report_hashes = [str(report.report_hash()) for report in transaction_reports]
    tree = MerkleTree(report_hashes)
    proofs: list[TransactionMerkleInclusionProof] = []
    for index, report in enumerate(transaction_reports):
        proof_steps = tuple(
            (step["position"], step["hash"]) for step in tree.get_proof(index)
        )
        proofs.append(
            TransactionMerkleInclusionProof(
                reference=str(report.reference),
                transaction_report_hash=report_hashes[index],
                index=index,
                merkle_root=tree.get_root(),
                proof_steps=proof_steps,
            )
        )
    return tuple(proofs)


def build_transaction_zk_attestations(
    inclusion_proofs: Sequence[TransactionMerkleInclusionProof],
    *,
    audit_merkle_root: str,
    transaction_count: int,
) -> tuple[TransactionZKAttestation, ...]:
    prover = AfriPayTransactionZKProver()
    verifier = MockSNARKVerifier()
    attestations: list[TransactionZKAttestation] = []
    for inclusion_proof in inclusion_proofs:
        input_data = {
            "reference": inclusion_proof.reference,
            "transaction_report_hash": inclusion_proof.transaction_report_hash,
            "index": inclusion_proof.index,
            "merkle_root": inclusion_proof.merkle_root,
            "proof_steps": [
                {"position": position, "hash": sibling_hash}
                for position, sibling_hash in inclusion_proof.proof_steps
            ],
        }
        output_data = {
            "audit_merkle_root": audit_merkle_root,
            "transaction_count": transaction_count,
            "reference": inclusion_proof.reference,
        }
        proof = prover.prove(input_data, output_data)
        verified = verifier.verify(proof)
        attestations.append(
            TransactionZKAttestation(
                reference=inclusion_proof.reference,
                proof=proof,
                verification_status="VERIFIED" if verified else "REJECTED",
            )
        )
    return tuple(attestations)


def _proof_as_dicts(proof_steps: tuple[tuple[str, str], ...]) -> list[dict[str, str]]:
    return [{"position": position, "hash": sibling_hash} for position, sibling_hash in proof_steps]

