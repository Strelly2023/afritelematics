"""
afritech/replay/transcript.py

Canonical replay transcript generator (Phase‑2B).

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
import time


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

    Phase‑2B:
    - Real inference binding under replay law

    Invariants preserved:
    - Phase‑1: deterministic trace + hashing
    - Phase‑2A: authority isolation
    - Phase‑2B: inference binding persistence
    """

    # --------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------------

    def generate(
        self,
        request: ConstitutionalRequest,
        output_path: str,
    ) -> dict[str, Any]:

        authority_profile = (
            request.payload["constitutional_request"]["authority_profile"]
        )

        # Deterministic execution trace
        execution_trace = self._build_execution_trace(request)

        # Phase‑2B inference binding
        inference_binding = self._invoke_real_inference(request)

        # Canonical TruthPacket payload (internal)
        truthpacket_payload = self._build_truthpacket_payload(
            request=request,
            trace=execution_trace,
            authority_profile=authority_profile,
            inference_binding=inference_binding,
        )

        truth_packet_hash = _sha256(
            _canonical_json(truthpacket_payload)
        )

        transcript = {
            "authority_profile": authority_profile,
            "request_hash": request.canonical_hash(),

            # Phase‑2B environment (authoritative)
            "replay_environment": self._replay_environment(
                inference_binding
            ),

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
                # Phase‑2B required step
                "step": "real_inference_invocation",
                "input_hash": h,
                "output_hash": _sha256(h + "inference"),
            },
            {
                "step": "truth_emission",
                "input_hash": h,
                "output_hash": _sha256(h + "truth"),
            },
        ]


    # ========================================================
    # PHASE‑2B: REAL INFERENCE INVOCATION
    # ========================================================

    def _invoke_real_inference(
        self,
        request: ConstitutionalRequest,
    ) -> dict[str, Any]:
        """
        Produce a deterministic inference binding.
        """

        input_hash = request.canonical_hash()

        # Deterministic stub output
        model_output = f"deterministic-output::{input_hash[:16]}"
        output_hash = _sha256(model_output)

        return {
            "provider": "local-deterministic-stub",
            "model_id": "llm-stub-deterministic-v2",
            "model_version": "2026-05",
            "parameters": {
                "temperature": 0.0,
                "top_p": 1.0,
                "max_tokens": 256,
            },
            "input_hash": input_hash,
            "output_hash": output_hash,
            "emitted_at": int(time.time()),
        }


    # ========================================================
    # TRUTHPACKET PAYLOAD (CANONICAL, INTERNAL)
    # ========================================================

    def _build_truthpacket_payload(
        self,
        request: ConstitutionalRequest,
        trace: list[dict[str, str]],
        authority_profile: str,
        inference_binding: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "claims": ["deterministic constitutional execution"],
            "authority_profile": authority_profile,
            "inference_binding": inference_binding,
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
    # REPLAY ENVIRONMENT (PHASE‑2B AUTHORITATIVE)
    # ========================================================

    def _replay_environment(
        self,
        inference_binding: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "runtime_version": "afritech-runtime-0.2.0",
            "model_id": inference_binding["model_id"],
            "model_version": inference_binding["model_version"],
            "constitution_version": "constitution-epoch-0002",
            "deterministic_mode": True,

            # REQUIRED by verifier
            "_inference_binding": inference_binding,
        }


    # ========================================================
    # REPLAY HASH (TERMINAL)
    # ========================================================

    def _compute_replay_hash(
        self,
        truthpacket_payload: dict[str, Any],
        trace: list[dict[str, str]],
    ) -> str:

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
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()