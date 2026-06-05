from __future__ import annotations


class ConsensusError(RuntimeError):
    """Base consensus failure."""


class ProofValidationError(ConsensusError):
    """Raised when proofs fail pre-consensus validation."""


class QuorumNotReached(ConsensusError):
    """Raised when accepted proofs do not satisfy quorum."""


class ConsensusTieError(ConsensusError):
    """Raised when no deterministic winner can be selected."""
