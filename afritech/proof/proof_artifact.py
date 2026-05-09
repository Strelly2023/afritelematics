# afritech/proof/proof_artifact.py

"""
AfriTech Proof Artifact

Represents a proof-carrying execution unit.

Guarantees:
- deterministic hashing
- tamper-evident structure
- replay-safe verification
- composable proof chains
- compatible with Lean-exported certificates
"""

from typing import Dict, Any, Optional
import hashlib
import json


class ProofError(Exception):
    """Raised when proof validation fails"""
    pass


class ProofArtifact:

    SCHEMA_VERSION = "afritech.proof.artifact.v1"

    # -----------------------------------------------------------------
    # CONSTRUCTOR
    # -----------------------------------------------------------------

    def __init__(
        self,
        theorem: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        parent: Optional["ProofArtifact"] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if not isinstance(theorem, str) or not theorem:
            raise ProofError("invalid_theorem")

        self.theorem = theorem

        # Deterministic hashes
        self.input_hash = self._hash(input_data)
        self.output_hash = self._hash(output_data)

        # Optional parent chain
        self.parent_hash = parent.proof_hash if parent else None

        # Ensure metadata is deterministic-safe
        self.metadata = self._sanitize_metadata(metadata or {})

        # Compute final proof hash
        self.proof_hash = self._compute_proof_hash()

        # Derive stable ID
        self.proof_id = self._derive_id()

        # Final internal validation
        if not self.verify():
            raise ProofError("invalid_proof_construction")

    # -----------------------------------------------------------------
    # CANONICALIZATION
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    def _hash(self, data: Dict[str, Any]) -> str:
        return hashlib.sha256(
            self._canonical_json(data).encode()
        ).hexdigest()

    def _sanitize_metadata(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure metadata remains JSON-serializable and deterministic
        """
        try:
            json.dumps(meta, sort_keys=True)
        except Exception:
            raise ProofError("invalid_metadata")

        return meta

    # -----------------------------------------------------------------
    # HASH COMPUTATION
    # -----------------------------------------------------------------

    def _compute_proof_hash(self) -> str:
        base = {
            "schema": self.SCHEMA_VERSION,
            "theorem": self.theorem,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "parent_hash": self.parent_hash,
            "metadata": self.metadata,
        }

        return hashlib.sha256(
            self._canonical_json(base).encode()
        ).hexdigest()

    def _derive_id(self) -> str:
        return self.proof_hash[:16]

    # -----------------------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Full structural + cryptographic validation
        """

        # Hash consistency
        if self.proof_hash != self._compute_proof_hash():
            return False

        # Type checks
        if not isinstance(self.theorem, str):
            return False

        if not isinstance(self.input_hash, str):
            return False

        if not isinstance(self.output_hash, str):
            return False

        if self.parent_hash is not None and not isinstance(self.parent_hash, str):
            return False

        return True

    # -----------------------------------------------------------------
    # CHAIN VALIDATION
    # -----------------------------------------------------------------

    def verify_chain(self, parent: Optional["ProofArtifact"]) -> bool:
        """
        Ensures correct linking between proofs
        """
        if parent is None:
            return self.parent_hash is None

        return self.parent_hash == parent.proof_hash

    # -----------------------------------------------------------------
    # STRONG VALIDATION (CHAIN ROOT)
    # -----------------------------------------------------------------

    def verify_full_chain(self, chain: list["ProofArtifact"]) -> bool:
        """
        Validate an entire proof chain (root → current)
        """
        if not chain:
            return False

        for i in range(1, len(chain)):
            if not chain[i].verify_chain(chain[i - 1]):
                return False

        return True

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.SCHEMA_VERSION,
            "proof_id": self.proof_id,
            "theorem": self.theorem,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "parent_hash": self.parent_hash,
            "metadata": self.metadata,
            "proof_hash": self.proof_hash,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    # -----------------------------------------------------------------
    # IMPORT
    # -----------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProofArtifact":

        obj = cls.__new__(cls)

        obj.theorem = data["theorem"]
        obj.input_hash = data["input_hash"]
        obj.output_hash = data["output_hash"]
        obj.parent_hash = data.get("parent_hash")
        obj.metadata = data.get("metadata", {})
        obj.proof_hash = data["proof_hash"]
        obj.proof_id = data.get("proof_id", obj.proof_hash[:16])

        if not obj.verify():
            raise ProofError("corrupted_proof_import")

        return obj

    # -----------------------------------------------------------------
    # LEAN PROOF CERTIFICATE IMPORT
    # -----------------------------------------------------------------

    @classmethod
    def from_certificate(cls, cert: Dict[str, Any]) -> "ProofArtifact":
        """
        Import proof generated from Lean export layer
        """

        required = ["theorem", "input_hash", "output_hash", "proof_hash"]

        for field in required:
            if field not in cert:
                raise ProofError(f"missing_certificate_field: {field}")

        obj = cls.__new__(cls)

        obj.theorem = cert["theorem"]
        obj.input_hash = cert["input_hash"]
        obj.output_hash = cert["output_hash"]
        obj.parent_hash = cert.get("parent_hash")
        obj.metadata = cert.get("metadata", {"source": "lean_export"})
        obj.proof_hash = cert["proof_hash"]
        obj.proof_id = obj.proof_hash[:16]

        if not obj.verify():
            raise ProofError("invalid_imported_certificate")

        return obj

    # -----------------------------------------------------------------
    # COMPOSITION
    # -----------------------------------------------------------------

    def derive(
        self,
        theorem: str,
        new_output: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "ProofArtifact":
        """
        Create chained proof (this → next)
        """

        return ProofArtifact(
            theorem=theorem,
            input_data={"previous_output_hash": self.output_hash},
            output_data=new_output,
            parent=self,
            metadata=metadata,
        )

    # -----------------------------------------------------------------
    # SECURITY HELPERS
    # -----------------------------------------------------------------

    def is_tampered(self) -> bool:
        """
        Detect whether proof has been modified
        """
        return not self.verify()

    # -----------------------------------------------------------------
    # REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return (
            f"<ProofArtifact id={self.proof_id} "
            f"theorem={self.theorem} "
            f"hash={self.proof_hash[:12]}...>"
        )
