"""
afritech/proof/runtime_certificate.py

Runtime Certificate
===================

Represents the highest level of execution legitimacy.

Binds:
- Registry state
- Execution context
- Execution result
- Proof snapshot

Responsibilities:
- Certify that execution is constitutionally valid
- Provide audit-grade verification artifact
- Enable replay validation
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

from runtime.context.runtime_context import RuntimeContext
from runtime.engine.executor import ExecutionResult
from proof.proof_snapshot import ProofSnapshot


# -----------------------------------------------------------------
# CERTIFICATE ERROR
# -----------------------------------------------------------------

class RuntimeCertificateError(Exception):
    pass


# -----------------------------------------------------------------
# RUNTIME CERTIFICATE
# -----------------------------------------------------------------

class RuntimeCertificate:

    def __init__(
        self,
        registry_hash: str,
        context: RuntimeContext,
        execution_result: ExecutionResult,
        proof_snapshot: ProofSnapshot,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        :param registry_hash: cryptographic identity of registry
        :param context: execution context
        :param execution_result: execution output
        :param proof_snapshot: proof snapshot object
        :param metadata: optional additional metadata
        """

        if not context or not execution_result or not proof_snapshot:
            raise RuntimeCertificateError("Missing required components")

        if not isinstance(context, RuntimeContext):
            raise RuntimeCertificateError("Invalid RuntimeContext")

        if not isinstance(execution_result, ExecutionResult):
            raise RuntimeCertificateError("Invalid ExecutionResult")

        if not isinstance(proof_snapshot, ProofSnapshot):
            raise RuntimeCertificateError("Invalid ProofSnapshot")

        if not execution_result.verify():
            raise RuntimeCertificateError("ExecutionResult integrity failed")

        if not proof_snapshot.verify():
            raise RuntimeCertificateError("ProofSnapshot integrity failed")

        if context.context_hash != proof_snapshot.context.context_hash:
            raise RuntimeCertificateError(
                "Context mismatch between execution and proof snapshot"
            )

        self.registry_hash = registry_hash
        self.context = context
        self.execution_result = execution_result
        self.proof_snapshot = proof_snapshot
        self.metadata = metadata or {}

        self.created_at = datetime.utcnow().isoformat() + "Z"

        # Deterministic certificate identity
        self.canonical = self._canonical_form()
        self.certificate_hash = self._compute_hash()

    # -----------------------------------------------------------------
    # CANONICAL FORM
    # -----------------------------------------------------------------

    def _canonical_form(self) -> Dict[str, Any]:
        return {
            "registry_hash": self.registry_hash,
            "context_hash": self.context.context_hash,
            "result_hash": self.execution_result.result_hash,
            "proof_hash": self.proof_snapshot.proof_hash,
            "metadata": self.metadata,
        }

    # -----------------------------------------------------------------
    # HASH
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _compute_hash(self) -> str:
        return hashlib.sha256(
            self._canonical_json(self.canonical).encode()
        ).hexdigest()

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_hash": self.certificate_hash,
            "created_at": self.created_at,
            "registry_hash": self.registry_hash,
            "context": self.context.to_dict(),
            "execution_result": self.execution_result.to_dict(),
            "proof_snapshot": self.proof_snapshot.to_dict(),
            "metadata": self.metadata,
        }

    # -----------------------------------------------------------------
    # VERIFY
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Full certificate integrity check
        """

        # Check internal integrity
        if not self.execution_result.verify():
            return False

        if not self.proof_snapshot.verify():
            return False

        if not self.context.verify():
            return False

        # Recompute hash
        recomputed = hashlib.sha256(
            self._canonical_json(self.canonical).encode()
        ).hexdigest()

        return recomputed == self.certificate_hash

    # -----------------------------------------------------------------
    # SIGNATURE HOOK
    # -----------------------------------------------------------------

    def sign(self, signer_id: str) -> Dict[str, Any]:
        """
        Placeholder for cryptographic signing
        """

        return {
            "signer": signer_id,
            "certificate_hash": self.certificate_hash,
            "signed_at": datetime.utcnow().isoformat() + "Z",
        }

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<RuntimeCertificate hash={self.certificate_hash[:10]}...>"


# -----------------------------------------------------------------
# FACTORY FUNCTION
# -----------------------------------------------------------------

def build_runtime_certificate(
    registry_hash: str,
    context: RuntimeContext,
    execution_result: ExecutionResult,
    proof_snapshot: ProofSnapshot,
    metadata: Optional[Dict[str, Any]] = None,
) -> RuntimeCertificate:
    """
    Convenience builder
    """

    return RuntimeCertificate(
        registry_hash=registry_hash,
        context=context,
        execution_result=execution_result,
        proof_snapshot=proof_snapshot,
        metadata=metadata,
    )