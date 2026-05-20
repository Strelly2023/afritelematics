# afritech/runtime/guards/proof_validator.py

"""
AfriTech Proof Validator

Purpose:
Validate proof-carrying execution artifacts at runtime.

Guarantees:
- Only approved theorems are accepted
- Proof hash integrity is enforced
- Input/output binding is verified
- Proof chains are validated
- Tampering is detected immediately
- TRACE can attest validation causality

This is the enforcement layer of Proof-Carrying Execution (PCE).
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from afritech.proof.proof_artifact import (
    ProofArtifact,
    ProofError,
)

from afritech.trace.trace_engine import TraceEngine


# -----------------------------------------------------------------
# ERROR
# -----------------------------------------------------------------

class ProofValidationError(Exception):
    """Raised when proof validation fails"""
    pass


# -----------------------------------------------------------------
# PROOF VALIDATOR
# -----------------------------------------------------------------

class ProofValidator:
    """
    Runtime Proof Validation Engine
    """

    # -------------------------------------------------------------
    # APPROVED THEOREMS (MUST MATCH LEAN EXPORT)
    # -------------------------------------------------------------

    APPROVED_THEOREMS = {
        "execution_deterministic",
        "no_hidden_execution",
        "admission_required",
        "surface_must_be_declared",
        "closed_world_execution",
    }

    # -------------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # -------------------------------------------------------------

    @classmethod
    def validate(
        cls,
        proof: ProofArtifact,
        *,
        expected_input_hash: str,
        expected_output_hash: str,
        parent: Optional[ProofArtifact] = None,
        trace: Optional[TraceEngine] = None,
    ) -> bool:
        """
        Full validation pipeline.

        Raises:
            ProofValidationError if ANY constraint fails
        """

        if trace:
            trace.record(
                "proof_validation_start",
                {
                    "theorem": getattr(proof, "theorem", None),
                },
            )

        cls._validate_structure(proof)
        cls._validate_integrity(proof)
        cls._validate_theorem(proof)
        cls._validate_binding(
            proof,
            expected_input_hash,
            expected_output_hash,
        )

        if parent is not None:
            cls._validate_chain(proof, parent)

        if trace:
            trace.complete(
                "proof_validation_start",
                {"status": "valid"},
            )

        return True

    # -------------------------------------------------------------
    # CORE VALIDATIONS
    # -------------------------------------------------------------

    @staticmethod
    def _validate_structure(proof: ProofArtifact) -> None:
        if not isinstance(proof, ProofArtifact):
            raise ProofValidationError("invalid_proof_type")

        if proof.is_tampered():
            raise ProofValidationError("tampered_proof_detected")

    @staticmethod
    def _validate_integrity(proof: ProofArtifact) -> None:
        try:
            if not proof.verify():
                raise ProofValidationError(
                    "proof_integrity_failure"
                )
        except ProofError as e:
            raise ProofValidationError(
                f"proof_verification_error: {e}"
            )

    @classmethod
    def _validate_theorem(cls, proof: ProofArtifact) -> None:
        if proof.theorem not in cls.APPROVED_THEOREMS:
            raise ProofValidationError(
                f"unapproved_theorem: {proof.theorem}"
            )

    @staticmethod
    def _validate_binding(
        proof: ProofArtifact,
        expected_input_hash: str,
        expected_output_hash: str,
    ) -> None:
        if proof.input_hash != expected_input_hash:
            raise ProofValidationError(
                "input_hash_mismatch"
            )

        if proof.output_hash != expected_output_hash:
            raise ProofValidationError(
                "output_hash_mismatch"
            )

    # -------------------------------------------------------------
    # CHAIN VALIDATION
    # -------------------------------------------------------------

    @staticmethod
    def _validate_chain(
        proof: ProofArtifact,
        parent: ProofArtifact,
    ) -> None:
        if not proof.verify_chain(parent):
            raise ProofValidationError(
                "invalid_proof_chain"
            )

    @classmethod
    def validate_chain_sequence(
        cls,
        chain: List[ProofArtifact],
        *,
        trace: Optional[TraceEngine] = None,
    ) -> bool:
        """
        Validate full proof chain (root → leaf).
        """

        if not chain:
            raise ProofValidationError(
                "empty_proof_chain"
            )

        for proof in chain:
            cls._validate_structure(proof)
            cls._validate_integrity(proof)
            cls._validate_theorem(proof)

        for i in range(1, len(chain)):
            if not chain[i].verify_chain(chain[i - 1]):
                raise ProofValidationError(
                    "broken_chain_link"
                )

        if trace:
            trace.record(
                "proof_chain_validation",
                {"length": len(chain)},
            )
            trace.complete(
                "proof_chain_validation",
                {"status": "valid"},
            )

        return True

    # -------------------------------------------------------------
    # CERTIFICATE VALIDATION (LEAN EXPORT)
    # -------------------------------------------------------------

    @classmethod
    def validate_certificate(
        cls,
        cert_data: Dict[str, Any],
        *,
        expected_input_hash: str,
        expected_output_hash: str,
        trace: Optional[TraceEngine] = None,
    ) -> ProofArtifact:
        """
        Validate raw certificate from Lean export.
        """

        proof = ProofArtifact.from_certificate(cert_data)

        cls.validate(
            proof,
            expected_input_hash=expected_input_hash,
            expected_output_hash=expected_output_hash,
            trace=trace,
        )

        return proof

    # -------------------------------------------------------------
    # STRICT MODE (MAX SECURITY)
    # -------------------------------------------------------------

    @classmethod
    def validate_strict(
        cls,
        proof: ProofArtifact,
        *,
        expected_input_hash: str,
        expected_output_hash: str,
        parent: Optional[ProofArtifact] = None,
        require_metadata: bool = False,
        trace: Optional[TraceEngine] = None,
    ) -> bool:
        """
        Strict validation mode.

        Includes:
        - all standard checks
        - optional metadata enforcement
        """

        cls.validate(
            proof,
            expected_input_hash=expected_input_hash,
            expected_output_hash=expected_output_hash,
            parent=parent,
            trace=trace,
        )

        if require_metadata and not proof.metadata:
            raise ProofValidationError(
                "missing_metadata"
            )

        return True

    # -------------------------------------------------------------
    # SAFE VALIDATION
    # -------------------------------------------------------------

    @classmethod
    def try_validate(
        cls,
        proof: ProofArtifact,
        *,
        expected_input_hash: str,
        expected_output_hash: str,
        parent: Optional[ProofArtifact] = None,
    ) -> bool:
        """
        Safe wrapper (no exception propagation).
        """

        try:
            return cls.validate(
                proof,
                expected_input_hash=expected_input_hash,
                expected_output_hash=expected_output_hash,
                parent=parent,
            )
        except ProofValidationError:
            return False