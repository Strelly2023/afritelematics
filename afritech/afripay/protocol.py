from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
import shutil
from pathlib import Path
from typing import Any, Iterable

from afritech.afripay.reconciliation import GlobalLedgerProof
from afritech.afripay.proofs import AfriPayTransactionZKProver
from afritech.audit.merkle import MerkleTree
from afritech.chain.anchor_publisher import publish_anchor
from afritech.chain.contracts.contract_client import verify_anchor_on_chain
from afritech.chain.types import ChainReceipt
from afritech.crypto.merkle import compute_merkle_root
from afritech.zk import Groth16Prover, Groth16Verifier, MockSNARKVerifier, ZKProof


@dataclass(frozen=True)
class RecursiveProofBundle:
    global_proof_hash: str
    child_proof_hashes: tuple[str, ...]
    recursive_merkle_root: str
    recursive_proof: ZKProof
    backend: str
    backend_verified: bool
    chain_receipt: ChainReceipt | None = None
    onchain_verified: bool = False
    authority_boundary: str = "recursive_proof_aggregates_child_commitments_only"

    @property
    def recursive_proof_hash(self) -> str:
        return self.recursive_proof.proof_hash

    @property
    def verified(self) -> bool:
        if len(self.global_proof_hash) != 64 or len(self.recursive_merkle_root) != 64:
            return False
        if not self.recursive_proof.verify() or not self.backend_verified:
            return False
        if self.chain_receipt is not None:
            if self.chain_receipt.proof_hash != self.recursive_proof_hash:
                return False
            if not self.onchain_verified:
                return False
        return True

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "authority_boundary": self.authority_boundary,
            "backend": self.backend,
            "backend_verified": self.backend_verified,
            "chain_receipt": self.chain_receipt.canonical_dict() if self.chain_receipt is not None else None,
            "child_proof_hashes": list(self.child_proof_hashes),
            "global_proof_hash": self.global_proof_hash,
            "onchain_verified": self.onchain_verified,
            "recursive_merkle_root": self.recursive_merkle_root,
            "recursive_proof": self.recursive_proof.to_dict(),
            "recursive_proof_hash": self.recursive_proof_hash,
            "schema": "afritech.afripay.recursive_proof_bundle.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


@dataclass(frozen=True)
class ProtocolAnchorVerification:
    proof_hash: str
    anchor_id: str
    chain_receipt: ChainReceipt
    onchain_verified: bool
    verified: bool
    authority_boundary: str = "onchain_anchor_commitment_only"

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "authority_boundary": self.authority_boundary,
            "chain_receipt": self.chain_receipt.canonical_dict(),
            "onchain_verified": self.onchain_verified,
            "proof_hash": self.proof_hash,
            "schema": "afritech.afripay.protocol_anchor_verification.v1",
            "verified": self.verified,
        }


def build_recursive_global_proof(
    global_proof: GlobalLedgerProof,
    *,
    anchor: bool = False,
    profile_name: str | None = None,
    require_live: bool = False,
) -> RecursiveProofBundle:
    child_proof_hashes = _recursive_child_hashes(global_proof)
    recursive_merkle_root = compute_merkle_root(list(child_proof_hashes))

    prover, verifier, backend = _select_recursive_backend()
    input_data = {
        "global_proof_hash": global_proof.global_proof_hash,
        "child_proof_hashes": list(child_proof_hashes),
        "ledger_merkle_root": global_proof.ledger_merkle_root,
        "audit_merkle_root": global_proof.audit_merkle_root,
        "recursive_merkle_root": recursive_merkle_root,
    }
    output_data = {
        "global_proof_hash": global_proof.global_proof_hash,
        "recursive_merkle_root": recursive_merkle_root,
        "transaction_count": global_proof.transaction_count,
    }
    recursive_proof = prover.prove(input_data, output_data)
    backend_verified = verifier.verify(recursive_proof)

    chain_receipt: ChainReceipt | None = None
    onchain_verified = False
    if anchor or profile_name is not None:
        chain_receipt = publish_anchor(
            recursive_proof.proof_hash,
            profile_name=profile_name,
            require_live=require_live,
        )
        anchor_id = _anchor_id(recursive_proof.proof_hash)
        onchain_verified = verify_anchor_on_chain(
            anchor_id,
            recursive_proof.proof_hash,
            profile_name=profile_name,
        )

    bundle = RecursiveProofBundle(
        global_proof_hash=global_proof.global_proof_hash,
        child_proof_hashes=child_proof_hashes,
        recursive_merkle_root=recursive_merkle_root,
        recursive_proof=recursive_proof,
        backend=backend,
        backend_verified=backend_verified,
        chain_receipt=chain_receipt,
        onchain_verified=onchain_verified,
    )
    if not bundle.verified:
        raise RuntimeError("recursive global proof failed")
    return bundle


def anchor_and_verify_protocol_proof(
    proof_hash: str,
    *,
    profile_name: str | None = None,
    require_live: bool = False,
) -> ProtocolAnchorVerification:
    anchor_id = _anchor_id(proof_hash)
    chain_receipt = publish_anchor(
        proof_hash,
        profile_name=profile_name,
        require_live=require_live,
    )
    onchain_verified = verify_anchor_on_chain(
        anchor_id,
        proof_hash,
        profile_name=profile_name,
    )
    verification = ProtocolAnchorVerification(
        proof_hash=proof_hash,
        anchor_id=anchor_id,
        chain_receipt=chain_receipt,
        onchain_verified=onchain_verified,
        verified=chain_receipt.proof_hash == proof_hash and onchain_verified,
    )
    if not verification.verified:
        raise RuntimeError("protocol proof anchor verification failed")
    return verification


def _recursive_child_hashes(global_proof: GlobalLedgerProof) -> tuple[str, ...]:
    child_hashes: list[str] = [
        *global_proof.transaction_report_hashes,
        *(proof.transaction_report_hash for proof in global_proof.transaction_inclusion_proofs),
        *(attestation.proof.proof_hash for attestation in global_proof.transaction_zk_attestations),
        global_proof.ledger_merkle_root,
        global_proof.provider_merkle_root,
        global_proof.event_merkle_root,
        global_proof.treasury_merkle_root,
        global_proof.global_proof_hash,
    ]
    return tuple(child_hashes)


def _select_recursive_backend() -> tuple[Any, Any, str]:
    wasm_path = os.getenv("AFRIPAY_GROTH16_WASM_PATH")
    zkey_path = os.getenv("AFRIPAY_GROTH16_ZKEY_PATH")
    verification_key_path = os.getenv("AFRIPAY_GROTH16_VERIFICATION_KEY_PATH")
    snarkjs_path = os.getenv("AFRIPAY_SNARKJS_PATH", "snarkjs")

    assets_available = all(
        [
            Groth16Prover is not None,
            Groth16Verifier is not None,
            wasm_path,
            zkey_path,
            verification_key_path,
            Path(str(wasm_path)).exists() if wasm_path else False,
            Path(str(zkey_path)).exists() if zkey_path else False,
            Path(str(verification_key_path)).exists() if verification_key_path else False,
            shutil.which(snarkjs_path) is not None,
        ]
    )

    if assets_available:
        prover = Groth16Prover(
            wasm_path=str(wasm_path),
            zkey_path=str(zkey_path),
            snarkjs_path=snarkjs_path,
        )
        verifier = Groth16Verifier(
            verification_key_path=str(verification_key_path),
            snarkjs_path=snarkjs_path,
        )
        return prover, verifier, "groth16"

    prover = AfriPayTransactionZKProver()
    verifier = MockSNARKVerifier()
    return prover, verifier, "mock"


def _anchor_id(proof_hash: str) -> str:
    return f"arch-{proof_hash[:12]}"


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()
