"""
afritech/zk/interface.py

AfriTech Zero-Knowledge Interface
=================================

Defines:
- ZKProof       → canonical proof container
- ZKProver      → abstract prover
- ZKVerifier    → abstract verifier
- ZKRegistry    → pluggable backend registry

Design guarantees:
- deterministic proof structure
- replay-safe hashing
- consensus compatibility
- runtime alignment (result_hash binding)
"""

from __future__ import annotations

from typing import Dict, Any, Optional
import json
import hashlib


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class ZKError(Exception):
    """Raised for any zk-related failure."""
    pass


# -----------------------------------------------------------------
# PROOF STRUCTURE
# -----------------------------------------------------------------

class ZKProof:
    """
    Canonical zero-knowledge proof container

    Properties:
    - deterministic hashing
    - canonical public inputs
    - backend-agnostic structure
    """

    def __init__(
        self,
        proof: bytes,
        public_inputs: Dict[str, Any],
        scheme: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):

        if not isinstance(proof, (bytes, bytearray)):
            raise ZKError("proof_must_be_bytes")

        if not isinstance(public_inputs, dict):
            raise ZKError("invalid_public_inputs")

        if not isinstance(scheme, str):
            raise ZKError("invalid_scheme")

        self.proof = bytes(proof)
        self.public_inputs = self._canonical(public_inputs)
        self.scheme = scheme
        self.metadata = metadata or {}

        self.proof_hash = self._compute_hash()

        if not self.verify():
            raise ZKError("invalid_zk_proof_structure")

    # ---------------------------------------------------------
    # CANONICAL JSON (DETERMINISTIC)
    # ---------------------------------------------------------

    def _canonical(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return json.loads(
                json.dumps(data, sort_keys=True, separators=(",", ":"))
            )
        except Exception:
            raise ZKError("non_serializable_public_inputs")

    # ---------------------------------------------------------
    # HASH (CRYPTOGRAPHIC IDENTITY)
    # ---------------------------------------------------------

    def _compute_hash(self) -> str:
        """
        Deterministic proof identity used by:
        - consensus
        - verification
        - audits
        """

        base = {
            "scheme": self.scheme,
            "public_inputs": self.public_inputs,
        }

        return hashlib.sha256(
            json.dumps(base, sort_keys=True, separators=(",", ":")).encode()
            + self.proof
        ).hexdigest()

    # ---------------------------------------------------------
    # VALIDATION
    # ---------------------------------------------------------

    def verify(self) -> bool:
        """
        Structural validation (NOT cryptographic verification)
        """

        return (
            isinstance(self.scheme, str)
            and isinstance(self.public_inputs, dict)
            and isinstance(self.proof, (bytes, bytearray))
            and len(self.proof) > 0
            and self.proof_hash == self._compute_hash()
        )

    # ---------------------------------------------------------
    # EXPORT
    # ---------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scheme": self.scheme,
            "public_inputs": self.public_inputs,
            "proof": self.proof.hex(),
            "proof_hash": self.proof_hash,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ZKProof":

        try:
            proof_bytes = bytes.fromhex(data["proof"])

            obj = cls(
                proof=proof_bytes,
                public_inputs=data["public_inputs"],
                scheme=data["scheme"],
                metadata=data.get("metadata", {}),
            )

            if obj.proof_hash != data.get("proof_hash"):
                raise ZKError("proof_hash_mismatch")

            return obj

        except KeyError as e:
            raise ZKError(f"missing_field: {e}")

    def __repr__(self):
        return f"<ZKProof scheme={self.scheme} hash={self.proof_hash[:12]}...>"


# -----------------------------------------------------------------
# PROVER
# -----------------------------------------------------------------

class ZKProver:
    """
    Abstract zk prover interface

    Must guarantee:
    - deterministic input handling
    - reproducible public inputs
    """

    scheme: str = "abstract"

    def prove(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ) -> ZKProof:
        raise NotImplementedError("prove() must be implemented")

    # ---------------------------------------------------------

    def _canonical_hash(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def build_public_inputs(
        self,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Default public input binding (aligned with runtime)

        output_hash must match ExecutionResult.result_hash
        """

        return {
            "input_hash": self._canonical_hash(input_data),
            "output_hash": self._canonical_hash(output_data),
        }


# -----------------------------------------------------------------
# VERIFIER
# -----------------------------------------------------------------

class ZKVerifier:
    """
    Abstract zk verifier interface
    """

    scheme: str = "abstract"

    def verify(self, proof: ZKProof) -> bool:
        raise NotImplementedError("verify() must be implemented")

    # ---------------------------------------------------------

    def verify_with_inputs(
        self,
        proof: ZKProof,
        expected_inputs: Dict[str, Any],
    ) -> bool:

        if not isinstance(proof, ZKProof):
            raise ZKError("invalid_proof_type")

        canonical_expected = json.loads(
            json.dumps(expected_inputs, sort_keys=True, separators=(",", ":"))
        )

        if proof.public_inputs != canonical_expected:
            return False

        return self.verify(proof)


# -----------------------------------------------------------------
# REGISTRY (BACKEND MANAGEMENT)
# -----------------------------------------------------------------

class ZKRegistry:
    """
    Registry for all zk verifier backends
    """

    _verifiers: Dict[str, ZKVerifier] = {}

    @classmethod
    def register(cls, scheme: str, verifier: ZKVerifier):
        if not isinstance(scheme, str):
            raise ZKError("invalid_scheme_name")

        if scheme in cls._verifiers:
            raise ZKError(f"duplicate_scheme: {scheme}")

        cls._verifiers[scheme] = verifier

    @classmethod
    def get_verifier(cls, scheme: str) -> ZKVerifier:
        if scheme not in cls._verifiers:
            raise ZKError(f"unknown_scheme: {scheme}")
        return cls._verifiers[scheme]

    @classmethod
    def verify(cls, proof: ZKProof) -> bool:
        verifier = cls.get_verifier(proof.scheme)
        return verifier.verify(proof)

    @classmethod
    def list_schemes(cls):
        return sorted(cls._verifiers.keys())
