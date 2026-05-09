"""
afritech/zk/registry.py

ZK Registry
===========

Central registry for ZK verification backends.

Responsibilities:
- Register verifiers per scheme
- Enforce uniqueness
- Route verification to correct backend
- Provide deterministic proof validation entrypoint
"""

from __future__ import annotations

from typing import Dict

from afritech.zk.interface import ZKVerifier, ZKProof, ZKError


# -----------------------------------------------------------------
# REGISTRY
# -----------------------------------------------------------------

class ZKRegistry:
    """
    Registry for all zk verifier backends

    Ensures:
    - unique scheme registration
    - safe lookup
    - consistent verification routing
    """

    _verifiers: Dict[str, ZKVerifier] = {}

    # -------------------------------------------------------------
    # REGISTER
    # -------------------------------------------------------------

    @classmethod
    def register(cls, scheme: str, verifier: ZKVerifier):
        """
        Register a verifier for a scheme
        """

        if not isinstance(scheme, str):
            raise ZKError("invalid_scheme_name")

        if not isinstance(verifier, ZKVerifier):
            raise ZKError("invalid_verifier_type")

        if scheme in cls._verifiers:
            raise ZKError(f"duplicate_scheme: {scheme}")

        # enforce scheme alignment
        verifier.scheme = scheme

        cls._verifiers[scheme] = verifier

    # -------------------------------------------------------------
    # GET VERIFIER
    # -------------------------------------------------------------

    @classmethod
    def get_verifier(cls, scheme: str) -> ZKVerifier:
        """
        Retrieve verifier for scheme
        """

        if scheme not in cls._verifiers:
            raise ZKError(f"unknown_scheme: {scheme}")

        return cls._verifiers[scheme]

    # -------------------------------------------------------------
    # VERIFY PROOF
    # -------------------------------------------------------------

    @classmethod
    def verify(cls, proof: ZKProof) -> bool:
        """
        Main verification entrypoint

        Validates:
        - proof structure
        - scheme existence
        - backend verification
        """

        if not isinstance(proof, ZKProof):
            raise ZKError("invalid_proof_object")

        # validate internal structure first
        if not proof.verify():
            raise ZKError("invalid_proof_structure")

        verifier = cls.get_verifier(proof.scheme)

        result = verifier.verify(proof)

        if not isinstance(result, bool):
            raise ZKError("verifier_must_return_bool")

        return result

    # -------------------------------------------------------------
    # VERIFY WITH EXPECTED INPUTS
    # -------------------------------------------------------------

    @classmethod
    def verify_with_inputs(
        cls,
        proof: ZKProof,
        expected_public_inputs: Dict,
    ) -> bool:
        """
        Verify proof AND ensure expected public inputs match
        """

        verifier = cls.get_verifier(proof.scheme)

        return verifier.verify_with_inputs(
            proof,
            expected_public_inputs
        )

    # -------------------------------------------------------------
    # LIST SCHEMES
    # -------------------------------------------------------------

    @classmethod
    def list_schemes(cls):
        return sorted(cls._verifiers.keys())

    # -------------------------------------------------------------
    # CLEAR (TESTING ONLY)
    # -------------------------------------------------------------

    @classmethod
    def clear(cls):
        """
        Reset registry (for testing environments)
        """
        cls._verifiers.clear()

    # -------------------------------------------------------------
    # STRING
    # -------------------------------------------------------------

    def __repr__(self):
        return f"<ZKRegistry schemes={list(self._verifiers.keys())}>"
