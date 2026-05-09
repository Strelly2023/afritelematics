"""
afritech/runtime/activation/activation_proof.py

Activation Proof Module

This module generates a deterministic, verifiable proof that the
runtime has successfully passed constitutional admission checks.

This proof acts as:
- Boot certificate
- Audit artifact
- Reproducibility reference
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any


class ActivationProofError(Exception):
    """Raised when activation proof generation fails"""
    pass


# -----------------------------------------------------------------
# ACTIVATION PROOF
# -----------------------------------------------------------------

class ActivationProof:

    def __init__(self, validator_state: Dict[str, Any]):
        """
        validator_state:
            Deterministic snapshot of validated runtime components
        """

        if not isinstance(validator_state, dict):
            raise ActivationProofError("validator_state must be a dict")

        self.validator_state = validator_state

        # Metadata
        self.timestamp = datetime.utcnow().isoformat() + "Z"

        # Deterministic artifacts
        self.canonical_state = self._canonical_json(validator_state)
        self.proof_hash = self._compute_hash(self.canonical_state)

    # -----------------------------------------------------------------
    # CANONICAL REPRESENTATION
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        """
        Ensure deterministic JSON structure
        """
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    # -----------------------------------------------------------------
    # HASH COMPUTATION
    # -----------------------------------------------------------------

    def _compute_hash(self, canonical: str) -> str:
        return hashlib.sha256(canonical.encode()).hexdigest()

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "validator_state": self.validator_state,
            "proof_hash": self.proof_hash
        }

    # -----------------------------------------------------------------
    # VERIFICATION
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Recompute hash and verify integrity
        """
        recomputed = self._compute_hash(self._canonical_json(self.validator_state))
        return recomputed == self.proof_hash

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<ActivationProof hash={self.proof_hash[:10]}...>"


# -----------------------------------------------------------------
# PROOF GENERATOR (UTILITY)
# -----------------------------------------------------------------

def generate_activation_proof(
    registry_hash: str,
    kernel_hash: str,
    epoch: int
) -> ActivationProof:
    """
    Convenience function used during runtime boot
    """

    validator_state = {
        "registry_hash": registry_hash,
        "kernel_hash": kernel_hash,
        "epoch": epoch
    }

    return ActivationProof(validator_state)


# -----------------------------------------------------------------
# OPTIONAL: FILE PERSISTENCE
# -----------------------------------------------------------------

def save_activation_proof(proof: ActivationProof, path: str) -> str:
    """
    Persist proof as canonical JSON file
    """

    try:
        with open(path, "w") as f:
            json.dump(
                proof.to_dict(),
                f,
                sort_keys=True,
                indent=2
            )

        return path

    except Exception as e:
        raise ActivationProofError(f"Failed to save proof: {str(e)}")


def load_activation_proof(path: str) -> ActivationProof:
    """
    Load proof and reconstruct object
    """

    try:
        with open(path, "r") as f:
            data = json.load(f)

        proof = ActivationProof(data["validator_state"])
        return proof

    except Exception as e:
        raise ActivationProofError(f"Failed to load proof: {str(e)}")