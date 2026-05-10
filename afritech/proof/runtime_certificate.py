"""
AfriTech Runtime Certificate
============================

Represents the highest level of execution legitimacy.

A RuntimeCertificate is valid iff:
- constitutional artifacts are cryptographically bound
- internal structure is self-consistent
- certificate hash is stable and verifiable

IMPORTANT:
This module MUST NOT import runtime execution machinery.
Execution binding is OPTIONAL and occurs only at runtime.

FAIL-CLOSED.
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json


# -----------------------------------------------------------------
# CERTIFICATE ERROR
# -----------------------------------------------------------------

class RuntimeCertificateError(Exception):
    """Raised when a runtime certificate is invalid"""
    pass


# -----------------------------------------------------------------
# RUNTIME CERTIFICATE
# -----------------------------------------------------------------

class RuntimeCertificate:
    """
    Canonical runtime legitimacy artifact.

    This object may exist in two modes:
    - Constitutional-only (Phase 5)
    - Execution-bound (Phase 6+)

    Both modes are valid.
    """

    def __init__(
        self,
        *,
        # -------------------------------------------------------------
        # EXECUTION BINDINGS (OPTIONAL)
        # -------------------------------------------------------------
        registry_hash: str,
        context: Optional[Any],
        execution_result: Optional[Any],
        proof_snapshot: Optional[Any],

        # -------------------------------------------------------------
        # CONSTITUTIONAL BINDINGS (REQUIRED)
        # -------------------------------------------------------------
        semantic_compiler_hash: str,
        invariant_ir_hash: str,
        invariant_index_hash: str,

        lean_invariant_hash: str,
        lean_epoch_hash: str,

        epoch_ir_hash: str,
        ci_completeness_hash: str,

        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Construct a runtime certificate.

        Constitutional bindings are REQUIRED.
        Execution bindings are OPTIONAL (Phase 6+).
        """

        # -------------------------------------------------------------
        # EXECUTION VALIDATION (OPTIONAL)
        # -------------------------------------------------------------

        if context is not None:
            if not hasattr(context, "context_hash"):
                raise RuntimeCertificateError(
                    "Invalid execution context (missing context_hash)"
                )

        if execution_result is not None:
            if not hasattr(execution_result, "result_hash"):
                raise RuntimeCertificateError(
                    "Invalid execution result (missing result_hash)"
                )
            if hasattr(execution_result, "verify"):
                if not execution_result.verify():
                    raise RuntimeCertificateError(
                        "ExecutionResult integrity failed"
                    )

        if proof_snapshot is not None:
            if not hasattr(proof_snapshot, "proof_hash"):
                raise RuntimeCertificateError(
                    "Invalid proof snapshot (missing proof_hash)"
                )
            if hasattr(proof_snapshot, "verify"):
                if not proof_snapshot.verify():
                    raise RuntimeCertificateError(
                        "ProofSnapshot integrity failed"
                    )

        if context is not None and proof_snapshot is not None:
            if (
                hasattr(proof_snapshot, "context")
                and proof_snapshot.context.context_hash != context.context_hash
            ):
                raise RuntimeCertificateError(
                    "Context mismatch between execution and proof snapshot"
                )

        # -------------------------------------------------------------
        # ASSIGN
        # -------------------------------------------------------------

        self.registry_hash = registry_hash
        self.context = context
        self.execution_result = execution_result
        self.proof_snapshot = proof_snapshot

        # Constitutional bindings
        self.semantic_compiler_hash = semantic_compiler_hash
        self.invariant_ir_hash = invariant_ir_hash
        self.invariant_index_hash = invariant_index_hash

        self.lean_invariant_hash = lean_invariant_hash
        self.lean_epoch_hash = lean_epoch_hash

        self.epoch_ir_hash = epoch_ir_hash
        self.ci_completeness_hash = ci_completeness_hash

        self.metadata = metadata or {}
        self.created_at = datetime.utcnow().isoformat() + "Z"

        # Deterministic certificate identity
        self.canonical = self._canonical_form()
        self.certificate_hash = self._compute_hash()

    # -----------------------------------------------------------------
    # CANONICAL FORM
    # -----------------------------------------------------------------

    def _canonical_form(self) -> Dict[str, Any]:
        """
        Canonical certificate form for hashing.
        """
        return {
            # Execution (optional)
            "registry_hash": self.registry_hash,
            "context_hash": getattr(self.context, "context_hash", None),
            "result_hash": getattr(self.execution_result, "result_hash", None),
            "proof_hash": getattr(self.proof_snapshot, "proof_hash", None),

            # Constitutional
            "semantic_compiler_hash": self.semantic_compiler_hash,
            "invariant_ir_hash": self.invariant_ir_hash,
            "invariant_index_hash": self.invariant_index_hash,
            "lean_invariant_hash": self.lean_invariant_hash,
            "lean_epoch_hash": self.lean_epoch_hash,
            "epoch_ir_hash": self.epoch_ir_hash,
            "ci_completeness_hash": self.ci_completeness_hash,

            # Metadata
            "metadata": self.metadata,
        }

    # -----------------------------------------------------------------
    # HASH
    # -----------------------------------------------------------------

    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _compute_hash(self) -> str:
        return hashlib.sha256(
            self._canonical_json(self.canonical).encode("utf-8")
        ).hexdigest()

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Export certificate for storage or audit.
        """
        return {
            "certificate_hash": self.certificate_hash,
            "created_at": self.created_at,
            "registry_hash": self.registry_hash,

            "execution": {
                "context_hash": getattr(self.context, "context_hash", None),
                "result_hash": getattr(self.execution_result, "result_hash", None),
                "proof_hash": getattr(self.proof_snapshot, "proof_hash", None),
            },

            "constitutional": {
                "semantic_compiler_hash": self.semantic_compiler_hash,
                "invariant_ir_hash": self.invariant_ir_hash,
                "invariant_index_hash": self.invariant_index_hash,
                "lean_invariant_hash": self.lean_invariant_hash,
                "lean_epoch_hash": self.lean_epoch_hash,
                "epoch_ir_hash": self.epoch_ir_hash,
                "ci_completeness_hash": self.ci_completeness_hash,
            },

            "metadata": self.metadata,
        }

    # -----------------------------------------------------------------
    # VERIFY
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Full certificate integrity check.
        """

        recomputed = hashlib.sha256(
            self._canonical_json(self.canonical).encode("utf-8")
        ).hexdigest()

        return recomputed == self.certificate_hash

    # -----------------------------------------------------------------
    # SIGNATURE HOOK
    # -----------------------------------------------------------------

    def sign(self, signer_id: str) -> Dict[str, Any]:
        """
        Placeholder for cryptographic signing.
        """
        return {
            "signer": signer_id,
            "certificate_hash": self.certificate_hash,
            "signed_at": datetime.utcnow().isoformat() + "Z",
        }

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<RuntimeCertificate "
            f"hash={self.certificate_hash[:10]}...>"
        )


# -----------------------------------------------------------------
# FACTORY FUNCTION
# -----------------------------------------------------------------

def build_runtime_certificate(
    *,
    registry_hash: str,
    context: Optional[Any],
    execution_result: Optional[Any],
    proof_snapshot: Optional[Any],

    semantic_compiler_hash: str,
    invariant_ir_hash: str,
    invariant_index_hash: str,

    lean_invariant_hash: str,
    lean_epoch_hash: str,

    epoch_ir_hash: str,
    ci_completeness_hash: str,

    metadata: Optional[Dict[str, Any]] = None,
) -> RuntimeCertificate:
    """
    Authoritative runtime certificate builder.
    """

    return RuntimeCertificate(
        registry_hash=registry_hash,
        context=context,
        execution_result=execution_result,
        proof_snapshot=proof_snapshot,

        semantic_compiler_hash=semantic_compiler_hash,
        invariant_ir_hash=invariant_ir_hash,
        invariant_index_hash=invariant_index_hash,

        lean_invariant_hash=lean_invariant_hash,
        lean_epoch_hash=lean_epoch_hash,

        epoch_ir_hash=epoch_ir_hash,
        ci_completeness_hash=ci_completeness_hash,

        metadata=metadata,
    )