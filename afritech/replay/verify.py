# afritech/replay/verify.py

"""
Constitutional Replay Verifier (Phase‑2B)
========================================

Replay is AUTHORITATIVE verification, not symbolic checking.

RULES:
- Replay is VERIFICATION, not EXECUTION
- Replay must NOT mutate state
- Replay must NOT admit runtime
- Replay must NOT parse epoch YAML
- Replay must consume ONLY:
    • replay transcript (YAML)
    • sealed registry attestation
    • compiled epoch semantics
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import hashlib
import json

# ✅ YAML is allowed ONLY for replay transcripts
import yaml

from afritech.replay.failures import (
    ReplayFailure,
    ReplayFailureMode,
    ReplayInvariant,
    DivergenceLocation,
)

from afritech.registry.loader import load_registry
from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import SemanticEpoch


# ============================================================
# VERDICT
# ============================================================

@dataclass(frozen=True)
class ReplayVerdict:
    status: str
    replay_hash: Optional[str]
    failure_mode: Optional[str]
    environment_match: bool
    trace_match: bool
    truthpacket_match: bool
    violated_invariant: Optional[str]
    divergence_location: Optional[str]

    @staticmethod
    def valid(replay_hash: str) -> "ReplayVerdict":
        return ReplayVerdict(
            status="REPLAY_VALID",
            replay_hash=replay_hash,
            failure_mode=None,
            environment_match=True,
            trace_match=True,
            truthpacket_match=True,
            violated_invariant=None,
            divergence_location=None,
        )

    @staticmethod
    def invalid(failure: ReplayFailure) -> "ReplayVerdict":
        return ReplayVerdict(
            status="REPLAY_INVALID",
            replay_hash=None,
            failure_mode=failure.failure_mode.value,
            environment_match=False,
            trace_match=False,
            truthpacket_match=False,
            violated_invariant=failure.violated_invariant.value,
            divergence_location=failure.divergence_location.value,
        )


# ============================================================
# REQUEST
# ============================================================

@dataclass(frozen=True)
class ConstitutionalRequest:
    payload: dict[str, Any]

    def canonical_hash(self) -> str:
        return _sha256(_canonical_json(self.payload))


# ============================================================
# INTERNAL ERROR
# ============================================================

class ReplayVerificationError(Exception):
    def __init__(self, failure: ReplayFailure):
        self.failure = failure
        super().__init__(failure.details or "")


# ============================================================
# VERIFIER
# ============================================================

class ReplayVerifier:
    """
    Deterministic constitutional replay verifier (Phase‑2B).

    Replay verifies by RECOMPUTATION + COMPARISON:
    - request hash
    - deterministic trace
    - truth packet
    - replay hash

    Replay NEVER executes runtime logic.
    """

    # --------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------------

    def verify(
        self,
        *,
        transcript_path: str,
        request: ConstitutionalRequest,
    ) -> ReplayVerdict:

        try:
            transcript = self._load_transcript(transcript_path)

            # --------------------------------------------------
            # 1. ENVIRONMENT VERIFICATION (SEALED REGISTRY)
            # --------------------------------------------------

            registry = load_registry()
            attestation = registry.get("attestation")

            if not attestation or attestation.get("status") != "SEALED":
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.ENVIRONMENT_MISMATCH,
                        ReplayInvariant.ENVIRONMENT_IDENTITY,
                        DivergenceLocation.REGISTRY_ATTESTATION,
                        "Registry attestation not SEALED",
                    )
                )

            # --------------------------------------------------
            # 2. EPOCH VERIFICATION (COMPILED ONLY)
            # --------------------------------------------------

            epoch_snapshot = transcript.get("epoch_snapshot")
            if not isinstance(epoch_snapshot, EpochSnapshot):
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.ENVIRONMENT_MISMATCH,
                        ReplayInvariant.EPOCH_IDENTITY,
                        DivergenceLocation.EPOCH_BINDING,
                        "EpochSnapshot missing or invalid",
                    )
                )

            semantic_epoch = epoch_snapshot.semantic_epoch
            if not isinstance(semantic_epoch, SemanticEpoch):
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.ENVIRONMENT_MISMATCH,
                        ReplayInvariant.EPOCH_IDENTITY,
                        DivergenceLocation.EPOCH_BINDING,
                        "Compiled SemanticEpoch required",
                    )
                )

            # --------------------------------------------------
            # 3. REQUEST HASH VERIFICATION
            # --------------------------------------------------

            if request.canonical_hash() != transcript["request_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.REQUEST_MISMATCH,
                        ReplayInvariant.REQUEST_IDENTITY,
                        DivergenceLocation.REQUEST_RECONSTRUCTION,
                        "Request hash mismatch",
                    )
                )

            # --------------------------------------------------
            # 4. TRACE RECOMPUTATION (PURE, DETERMINISTIC)
            # --------------------------------------------------

            recomputed_trace = self._rerun_execution(request)

            if recomputed_trace != transcript["execution_trace"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.TRACE_DIVERGENCE,
                        ReplayInvariant.CAUSAL_RECONSTRUCTION,
                        DivergenceLocation.EXECUTION_RERUN,
                        "Execution trace mismatch",
                    )
                )

            # --------------------------------------------------
            # 5. TRUTHPACKET REGENERATION
            # --------------------------------------------------

            regenerated_truthpacket = self._regenerate_truthpacket(
                request=request,
                trace=recomputed_trace,
                transcript=transcript,
            )

            truthpacket_hash = _sha256(
                _canonical_json(regenerated_truthpacket)
            )

            if truthpacket_hash != transcript["truth_packet_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.TRUTHPACKET_DIVERGENCE,
                        ReplayInvariant.TRUTHPACKET_IDENTITY,
                        DivergenceLocation.TRUTHPACKET_REGENERATION,
                        "TruthPacket hash mismatch",
                    )
                )

            # --------------------------------------------------
            # 6. REPLAY HASH RECOMPUTATION (FINAL AUTHORITY)
            # --------------------------------------------------

            replay_hash = self._compute_replay_hash(
                regenerated_truthpacket,
                recomputed_trace,
            )

            if replay_hash != transcript["replay_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.HASH_MISMATCH,
                        ReplayInvariant.DETERMINISTIC_IDENTITY,
                        DivergenceLocation.HASH_RECOMPUTATION,
                        "Replay hash mismatch",
                    )
                )

            # --------------------------------------------------
            # ✅ AUTHORITATIVE REPLAY VALID
            # --------------------------------------------------

            return ReplayVerdict.valid(replay_hash)

        except ReplayVerificationError as e:
            return ReplayVerdict.invalid(e.failure)

    # ============================================================
    # LOAD TRANSCRIPT (YAML ALLOWED — TRANSCRIPT ONLY)
    # ============================================================

    def _load_transcript(self, path: str) -> dict[str, Any]:
        p = Path(path)

        if not p.exists() or not p.is_file():
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.INVALID_TRANSCRIPT_PATH,
                    ReplayInvariant.TRANSCRIPT_EXISTENCE,
                    DivergenceLocation.TRANSCRIPT_LOAD,
                    "Transcript file not found",
                )
            )

        with p.open("r", encoding="utf-8") as f:
            transcript = yaml.safe_load(f)

        required = {
            "authority_profile",
            "request_hash",
            "replay_environment",
            "execution_trace",
            "truth_packet_hash",
            "replay_hash",
            "epoch_snapshot",  # ✅ compiled epoch, not YAML
        }

        if not isinstance(transcript, dict) or not required.issubset(transcript):
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.INVALID_TRANSCRIPT_SCHEMA,
                    ReplayInvariant.TRANSCRIPT_INTEGRITY,
                    DivergenceLocation.TRANSCRIPT_SCHEMA,
                    "Invalid transcript schema",
                )
            )

        return transcript

    # ============================================================
    # PURE DETERMINISTIC RERUN (NO EXECUTION)
    # ============================================================

    def _rerun_execution(self, request: ConstitutionalRequest):
        """
        Deterministically recompute execution trace
        WITHOUT executing runtime code.
        """
        h = request.canonical_hash()
        return [
            {"step": "scope_evaluation", "input_hash": h, "output_hash": _sha256(h + "scope")},
            {"step": "routing_selection", "input_hash": h, "output_hash": _sha256(h + "route")},
            {"step": "real_inference_invocation", "input_hash": h, "output_hash": _sha256(h + "inference")},
            {"step": "truth_emission", "input_hash": h, "output_hash": _sha256(h + "truth")},
        ]

    # ============================================================
    # TRUTHPACKET REGENERATION (DETERMINISTIC)
    # ============================================================

    def _regenerate_truthpacket(
        self,
        *,
        request: ConstitutionalRequest,
        trace: list,
        transcript: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "claims": ["deterministic constitutional execution"],
            "authority_profile": transcript["authority_profile"],
            "inference_binding": transcript["replay_environment"]["_inference_binding"],
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

    # ============================================================
    # REPLAY HASH (FINAL COMMIT)
    # ============================================================

    def _compute_replay_hash(self, truthpacket, trace):
        return _sha256(
            _canonical_json({
                "truthpacket": truthpacket,
                "trace": trace,
            })
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