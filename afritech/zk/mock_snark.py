"""ch/zk/mock_snark.py

Mock SNARK Verifier
===================

Deterministic placeholder verifier for testing.

Guarantees:
- deterministic verification
- public input binding
- replay safety
- structure validation

NOTE:
This is NOT cryptographically secure.
It is only for testing and development.
"""

from __future__ import annotations

from typing import Dict, Any
import json
import hashlib

from afritech.zk.interface import ZKVerifier, ZKProof, ZKError


# -----------------------------------------------------------------
# MOCK SNARK VERIFIER
# -----------------------------------------------------------------

class MockSNARKVerifier(ZKVerifier):
    """
    Mock verifier using deterministic hashing.

    Verification rule:

        proof == SHA256(canonical(public_inputs))

    This simulates proof binding without real ZK cryptography.
    """

    scheme = "mock"

    # -------------------------------------------------------------
    # VERIFY
    # -------------------------------------------------------------

    def verify(self, proof: ZKProof) -> bool:

        # ---------------------------------------------------------
        # STRUCTURAL VALIDATION
        # ---------------------------------------------------------
        if not isinstance(proof, ZKProof):
            raise ZKError("invalid_proof_object")

        if not proof.verify():
            raise ZKError("invalid_proof_structure")

        if proof.scheme != self.scheme:
            raise ZKError(f"scheme_mismatch: expected {self.scheme}")

        # ---------------------------------------------------------
        # CANONICALIZE PUBLIC INPUTS
        # ---------------------------------------------------------
        canonical_inputs = self._canonical(proof.public_inputs)

        # ---------------------------------------------------------
        # RECONSTRUCT EXPECTED PROOF
        # ---------------------------------------------------------
        expected = hashlib.sha256(
            json.dumps(
                canonical_inputs,
                sort_keys=True,
                separators=(",", ":")
            ).encode()
        ).digest()

        # ---------------------------------------------------------
        # VERIFY MATCH
        # ---------------------------------------------------------
        if proof.proof != expected:
            return False

        # ---------------------------------------------------------
        # ADDITIONAL SAFETY (OPTIONAL BUT STRONG)
        # ---------------------------------------------------------
        # ensure proof_hash consistency
        recomputed_hash = hashlib.sha256(
            json.dumps(
                {
                    "scheme": proof.scheme,
                    "public_inputs": canonical_inputs,
                },
                sort_keys=True,
                separators=(",", ":")
            ).encode() + proof.proof
        ).hexdigest()

        if recomputed_hash != proof.proof_hash:
            raise ZKError("proof_hash_mismatch")

        return True

    # -------------------------------------------------------------
    # CANONICALIZATION
    # -------------------------------------------------------------

    def _canonical(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return json.loads(
                json.dumps(data, sort_keys=True, separators=(",", ":"))
            )
        except Exception:
            raise ZKError("non_serializable_public_inputs")

