"""
afritech/replay/transcript.py

Canonical replay transcript generator.

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
- afritech/replay/REPLAY_VERIFIER_SPEC.md
- afritech/replay/VERIFY_INTERFACE_SPEC.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import yaml


# ============================================================
# REQUEST
# ============================================================

@dataclass(frozen=True)
class ConstitutionalRequest:
    """
    Immutable wrapper for a constitutional request payload.
    """
    payload: dict[str, Any]

    def canonical_hash(self) -> str:
        """
        Canonical hash of the request payload.
        """
        return _sha256(_canonical_json(self.payload))


# ============================================================
# TRANSCRIPT GENERATOR
# ============================================================

class ReplayTranscriptGenerator:
    """
    Deterministic transcript generator for constitutional replay.

    Responsibilities:
    - build deterministic execution trace
    - construct TruthPacket payload (internal only)
    - emit replay-valid transcript (hash-authoritative)

    Phase-2A Invariant:
    - Authority identity MUST be explicit and replay-bound
    """

    def generate(
        self,
        request: ConstitutionalRequest,
        output_path: str,
    ) -> dict[str, Any]:
        """
        Generate and persist a replay transcript.
        """

        # ----------------------------
        # Authority binding (Phase-2A)
        # ----------------------------
        authority_profile = (
            request.payload["constitutional_request"]["authority_profile"]
        )

        # ----------------------------
        # Deterministic execution trace
        # ----------------------------
        execution_trace = self._build_execution_trace(request)

        # ----------------------------
        # TruthPacket payload (internal)
        # ----------------------------
        truthpacket_payload = self._build_truthpacket_payload(
            request=request,
            trace=execution_trace,
            authority_profile=authority_profile,
        )

        truth_packet_hash = _sha256(
            _canonical_json(truthpacket_payload)
        )

        # ----------------------------
        # Final transcript
        # ----------------------------
        transcript = {
            # Phase-2A authority binding
            "authority_profile": authority_profile,

            # Phase-1 invariants
            "request_hash": request.canonical_hash(),
            "replay_environment": self._replay_environment(),
            "execution_trace": execution_trace,
            "truth_packet_hash": truth_packet_hash,
            "replay_hash": self._compute_replay_hash(
                truthpacket_payload,
                execution_trace,
            ),
        }

        self._write_transcript(transcript, output_path)
        return transcript


    # ========================================================
    # EXECUTION TRACE (DETERMINISTIC)
    # ========================================================

    def _build_execution_trace(
        self,
        request: ConstitutionalRequest,
    ) -> list[dict[str, str]]:
        """
        Construct a deterministic execution trace based solely
        on the canonical request hash.
        """

        h = request.canonical_hash()

        return [
            {
                "step": "scope_evaluation",
                "input_hash": h,
                "output_hash": _sha256(h + "scope"),
            },
            {
                "step": "routing_selection",
                "input_hash": h,
                "output_hash": _sha256(h + "route"),
            },
            {
                "step": "truth_emission",
                "input_hash": h,
                "output_hash": _sha256(h + "truth"),
            },
        ]


    # ========================================================
    # TRUTHPACKET PAYLOAD (INTERNAL ONLY)
    # ========================================================

    def _build_truthpacket_payload(
        self,
        request: ConstitutionalRequest,
        trace: list[dict[str, str]],
        authority_profile: str,
    ) -> dict[str, Any]:
        """
        Build the internal TruthPacket payload.
        """

        return {
            "claims": ["deterministic constitutional execution"],
            "authority_profile": authority_profile,
            "provenance_chain": trace,
            "epoch_id": request.payload["constitutional_request"]["epoch_id"],
            "epistemic_confidence": {
                "evidentiary": 1.0,
                "source_consensus": 1.0,
                "replay_determinism": 1.0,
                "attestation_strength": 0.0,
                "temporal_stability": 1.0,
            },
            "causal_trace": {
                "decisions": trace,
                "dependencies": [],
                "rejected_paths": [],
            },
        }


    # ========================================================
    # REPLAY ENVIRONMENT (BOUND)
    # ========================================================

    def _replay_environment(self) -> dict[str, Any]:
        """
        Declare the replay execution environment.
        """
        return {
            "runtime_version": "afritech-runtime-0.1.0",
            "model_version": "llm-stub-deterministic-v1",
            "constitution_version": "constitution-epoch-0001",
            "deterministic_mode": True,
        }


    # ========================================================
    # REPLAY HASH (TERMINAL)
    # ========================================================

    def _compute_replay_hash(
        self,
        truthpacket_payload: dict[str, Any],
        trace: list[dict[str, str]],
    ) -> str:
        """
        Compute the terminal replay hash from TruthPacket
        and execution trace.
        """

        return _sha256(
            _canonical_json(
                {
                    "truthpacket": truthpacket_payload,
                    "trace": trace,
                }
            )
        )


    # ========================================================
    # OUTPUT
    # ========================================================

    def _write_transcript(
        self,
        transcript: dict[str, Any],
        output_path: str,
    ) -> None:
        """
        Persist transcript to disk deterministically.
        """

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                transcript,
                f,
                sort_keys=True,
                allow_unicode=True,
            )


# ============================================================
# UTILITIES
# ============================================================

def _canonical_json(obj: Any) -> str:
    """
    Canonical JSON serialization for hashing.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(value: str) -> str:
    """
    SHA-256 hex digest helper.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
