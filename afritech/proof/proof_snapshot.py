"""
afritech/proof/proof_snapshot.py

Proof Snapshot
==============

Captures a deterministic, verifiable snapshot of execution.

Responsibilities:
- Bind context + output + metadata
- Generate cryptographic proof
- Support replay verification
- Provide audit-ready artifact
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

from runtime.context.runtime_context import RuntimeContext


# -----------------------------------------------------------------
# PROOF ERROR
# -----------------------------------------------------------------

class ProofSnapshotError(Exception):
    pass


# -----------------------------------------------------------------
# PROOF SNAPSHOT
# -----------------------------------------------------------------

class ProofSnapshot:

    def __init__(
        self,
        context: RuntimeContext,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        :param context: execution context
        :param result: execution output/result
        :param metadata: optional system metadata
        """

        if not isinstance(context, RuntimeContext):
            raise ProofSnapshotError("Invalid RuntimeContext")

        if not isinstance(result, dict):
            raise ProofSnapshotError("Result must be a dict")

        self.context = context
        self.result = result
        self.metadata = metadata or {}

        self.created_at = datetime.utcnow().isoformat() + "Z"

        # Deterministic proof identity
        self.canonical = self._canonical_form()
        self.proof_hash = self._compute_hash()

    # -----------------------------------------------------------------
    # CANONICAL FORM
    # -----------------------------------------------------------------

    def _canonical_form(self) -> Dict[str, Any]:
        """
        Defines deterministic snapshot structure
        """

        return {
            "context": {
                "context_hash": self.context.context_hash,
                "authority": self.context.authority_profile,
                "payload": self.context.payload,
                "replay_requirements": self.context.replay_requirements,
            },
            "result": self.result,
            "metadata": self.metadata,
        }

    # -----------------------------------------------------------------
    # HASH COMPUTATION
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
            "proof_hash": self.proof_hash,
            "created_at": self.created_at,
            "snapshot": self.canonical,
        }

    # -----------------------------------------------------------------
    # VERIFICATION
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Recompute hash to ensure snapshot integrity
        """
        recomputed = hashlib.sha256(
            self._canonical_json(self.canonical).encode()
        ).hexdigest()

        return recomputed == self.proof_hash

    # -----------------------------------------------------------------
    # SIGNATURE HOOK (FUTURE EXTENSION)
    # -----------------------------------------------------------------

    def sign(self, signer_id: str) -> Dict[str, Any]:
        """
        Placeholder for cryptographic signature

        Future:
        - private key signing
        - distributed node attestation
        """

        return {
            "signer": signer_id,
            "proof_hash": self.proof_hash,
            "signed_at": datetime.utcnow().isoformat() + "Z",
        }

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<ProofSnapshot hash={self.proof_hash[:10]}...>"


# -----------------------------------------------------------------
# FACTORY FUNCTION
# -----------------------------------------------------------------

def build_proof_snapshot(
    context: RuntimeContext,
    result: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> ProofSnapshot:
    """
    Convenience builder for snapshots
    """

    return ProofSnapshot(context, result, metadata)


# -----------------------------------------------------------------
# FILE PERSISTENCE (OPTIONAL)
# -----------------------------------------------------------------

def save_proof_snapshot(snapshot: ProofSnapshot, path: str) -> str:
    try:
        with open(path, "w") as f:
            json.dump(snapshot.to_dict(), f, indent=2, sort_keys=True)
        return path
    except Exception as e:
        raise ProofSnapshotError(f"Failed to save proof snapshot: {str(e)}")


def load_proof_snapshot(path: str) -> ProofSnapshot:
    try:
        with open(path, "r") as f:
            data = json.load(f)

        snapshot_data = data["snapshot"]

        dummy_context = RuntimeContext(
            authority_profile=snapshot_data["context"]["authority"],
            payload=snapshot_data["context"]["payload"],
            replay_requirements=snapshot_data["context"]["replay_requirements"],
        )

        snapshot = ProofSnapshot(
            context=dummy_context,
            result=snapshot_data["result"],
        )

        return snapshot

    except Exception as e:
        raise ProofSnapshotError(f"Failed to load proof snapshot: {str(e)}")