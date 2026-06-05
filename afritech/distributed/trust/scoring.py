from __future__ import annotations

from dataclasses import dataclass


VALID_PROOF = "valid_proof"
INVALID_PROOF = "invalid_proof"
TIMEOUT = "timeout"
CONSENSUS_MATCH = "consensus_match"
CONSENSUS_MISMATCH = "consensus_mismatch"


@dataclass(frozen=True)
class TrustScoreRules:
    valid_proof: float = 1.0
    invalid_proof: float = -20.0
    timeout: float = -5.0
    consensus_match: float = 2.0
    consensus_mismatch: float = -10.0

    def delta_for(self, event_type: str) -> float:
        if event_type == VALID_PROOF:
            return self.valid_proof
        if event_type == INVALID_PROOF:
            return self.invalid_proof
        if event_type == TIMEOUT:
            return self.timeout
        if event_type == CONSENSUS_MATCH:
            return self.consensus_match
        if event_type == CONSENSUS_MISMATCH:
            return self.consensus_mismatch
        raise ValueError(f"unknown trust event: {event_type}")
