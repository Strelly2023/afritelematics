"""
afritech/truth/packet.py

Canonical TruthPacket Emission

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import hashlib
import json


# ============================================================
# EXCEPTIONS
# ============================================================

class TruthPacketViolation(Exception):
    """
    Raised when TruthPacket construction violates constitutional rules.
    """
    pass


# ============================================================
# TRUTH PACKET (EPISTEMIC ARTIFACT)
# ============================================================

@dataclass(frozen=True)
class TruthPacket:
    """
    Replay-verifiable epistemic artifact.

    This object:
    - creates no authority
    - executes no intelligence
    - mutates no state
    """
    payload: Dict[str, Any]
    truth_packet_hash: str


# ============================================================
# TRUTH EMITTER
# ============================================================

class TruthPacketEmitter:
    """
    Deterministic constitutional TruthPacket constructor.
    """

    REQUIRED_AUTHORITY = "CONSTITUTIONAL_RESEARCH_AGENT"

    REQUIRED_EPISTEMIC_FIELDS = {
        "evidentiary",
        "source_consensus",
        "replay_determinism",
        "attestation_strength",
        "temporal_stability",
    }


    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def emit(
        self,
        arbitration_result: Any,
        dispatch_artifact: Any,
        execution_trace: List[Dict[str, str]],
        epoch_id: str,
    ) -> TruthPacket:

        self._validate_arbitration(arbitration_result)
        self._validate_dispatch(dispatch_artifact)

        epistemic_confidence = self._epistemic_confidence()

        payload = {
            "claims": [
                "deterministic constitutional execution"
            ],
            "authority_profile": arbitration_result.authority_profile,
            "provenance_chain": execution_trace,
            "epoch_id": epoch_id,
            "epistemic_confidence": epistemic_confidence,
            "causal_trace": {
                "decisions": arbitration_result.reasoning_trace,
                "dependencies": [],
                "rejected_paths": [],
            },
            "arbitration_id": arbitration_result.arbitration_id,
            "dispatch_id": dispatch_artifact.dispatch_id,
        }

        truth_packet_hash = self._hash(payload)

        return TruthPacket(
            payload=payload,
            truth_packet_hash=truth_packet_hash,
        )


    # ========================================================
    # VALIDATION
    # ========================================================

    def _validate_arbitration(
        self,
        arbitration_result: Any,
    ) -> None:

        if arbitration_result.permitted is not True:
            raise TruthPacketViolation(
                "Arbitration denied execution"
            )

        if arbitration_result.deterministic is not True:
            raise TruthPacketViolation(
                "Non-deterministic arbitration forbidden"
            )

        if arbitration_result.authority_profile != self.REQUIRED_AUTHORITY:
            raise TruthPacketViolation(
                "Invalid authority profile in arbitration result"
            )


    def _validate_dispatch(
        self,
        dispatch_artifact: Any,
    ) -> None:

        if dispatch_artifact.authority_profile != self.REQUIRED_AUTHORITY:
            raise TruthPacketViolation(
                "Invalid authority profile in dispatch artifact"
            )

        if dispatch_artifact.deterministic is not True:
            raise TruthPacketViolation(
                "Non-deterministic dispatch forbidden"
            )


    # ========================================================
    # EPISTEMIC CONFIDENCE (CANONICAL, DECOMPOSED)
    # ========================================================

    def _epistemic_confidence(self) -> Dict[str, float]:
        """
        Canonical normalized epistemic confidence vector.

        No aggregation.
        No interpretation.
        Replay-safe.
        """
        return {
            "evidentiary": 1.0,
            "source_consensus": 1.0,
            "replay_determinism": 1.0,
            "attestation_strength": 0.0,
            "temporal_stability": 1.0,
        }


    # ========================================================
    # HASHING (CANONICAL, TERMINAL)
    # ========================================================

    def _hash(
        self,
        payload: Dict[str, Any],
    ) -> str:

        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()