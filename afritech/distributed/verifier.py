from __future__ import annotations

from typing import List, Dict, Any
from collections import Counter
import json
import hashlib

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from afritech.distributed.proof import hash_result, validate_proof_structure


class ProofVerifier:
    """
    Zero-Trust Proof Verifier.

    Responsibilities:
    - Verify structure of proofs
    - Verify hash integrity
    - Verify cryptographic signatures
    - Enforce deterministic consensus
    """

    def __init__(self, public_keys: Dict[str, Ed25519PublicKey]) -> None:
        if not isinstance(public_keys, dict):
            raise TypeError("public_keys must be a dictionary")

        self.public_keys: Dict[str, Ed25519PublicKey] = public_keys

    # -----------------------------------------------------
    # Proof verification
    # -----------------------------------------------------

    def verify_proof(self, proof: Dict[str, Any]) -> bool:
        """
        Verify a single proof.

        Checks:
        - structure
        - hash integrity
        - signature validity
        """

        try:
            # ✅ Step 1: Structure validation
            if not validate_proof_structure(proof):
                return False

            node_id = proof["node"]
            result = proof["result"]
            signature_hex = proof["signature"]
            metadata = proof.get("metadata", {})

            if node_id not in self.public_keys:
                return False

            # ✅ Step 2: Rebuild canonical payload (MUST match signer!)
            payload = {
                "node": node_id,
                "result": result,
                "metadata": metadata,
            }

            message = self._serialize(payload)

            signature = bytes.fromhex(signature_hex)
            public_key = self.public_keys[node_id]

            # ✅ Step 3: Cryptographic verification
            public_key.verify(signature, message)

            return True

        except Exception:
            return False

    # -----------------------------------------------------
    # Consensus
    # -----------------------------------------------------

    def consensus(self, proofs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform zero-trust consensus across proofs.

        Returns:
        {
            "result": Any,
            "votes": int,
            "valid_proofs": int
        }
        """

        # ✅ Filter valid proofs only
        valid = [p for p in proofs if self.verify_proof(p)]

        if not valid:
            raise RuntimeError("All proofs invalid")

        # ✅ Deterministic hashing
        hashed_results = [
            hash_result(p["result"])
            for p in valid
        ]

        counts = Counter(hashed_results)
        consensus_hash, votes = counts.most_common(1)[0]

        # ✅ Majority enforcement
        if votes <= len(valid) // 2:
            raise RuntimeError("No consensus")

        # ✅ Retrieve consensus result
        consensus_result = next(
            p["result"]
            for p in valid
            if hash_result(p["result"]) == consensus_hash
        )

        return {
            "result": consensus_result,
            "votes": votes,
            "valid_proofs": len(valid),
        }

    # -----------------------------------------------------
    # Deterministic serialization
    # -----------------------------------------------------

    def _serialize(self, data: Dict[str, Any]) -> bytes:
        """
        Canonical serialization for signature verification.
        MUST match signing logic exactly.
        """

        try:
            serialized = json.dumps(
                data,
                sort_keys=True,
                separators=(",", ":"),  # ✅ remove whitespace
                default=str,
            )
        except Exception:
            serialized = str(data)

        return serialized.encode("utf-8")