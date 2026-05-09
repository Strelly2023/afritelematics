"""
afritech/replay/verify.py

Constitutional Replay Verifier (Phase‑2B).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import hashlib
import json
import yaml

from afritech.replay.failures import (
    ReplayFailure,
    ReplayFailureMode,
    ReplayInvariant,
    DivergenceLocation,
)


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
    """

    # --------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------------

    def verify(
        self,
        transcript_path: str,
        request: ConstitutionalRequest,
    ) -> ReplayVerdict:

        try:
            transcript = self._load_transcript(transcript_path)

            self._validate_authority(request, transcript)
            self._validate_environment(transcript)
            self._validate_request(request, transcript)

            rerun_trace = self._rerun_execution(request)
            self._compare_trace(transcript["execution_trace"], rerun_trace)

            truthpacket = self._regenerate_truthpacket(
                request, rerun_trace, transcript
            )

            self._validate_inference_binding(
                request,
                transcript,
                truthpacket["inference_binding"],
            )

            truthpacket_hash = _sha256(_canonical_json(truthpacket))
            if truthpacket_hash != transcript["truth_packet_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.TRUTHPACKET_DIVERGENCE,
                        ReplayInvariant.TRUTHPACKET_IDENTITY,
                        DivergenceLocation.TRUTHPACKET_REGENERATION,
                        "TruthPacket hash mismatch",
                    )
                )

            replay_hash = self._compute_replay_hash(truthpacket, rerun_trace)
            if replay_hash != transcript["replay_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        ReplayFailureMode.HASH_MISMATCH,
                        ReplayInvariant.DETERMINISTIC_IDENTITY,
                        DivergenceLocation.HASH_RECOMPUTATION,
                        "Replay hash mismatch",
                    )
                )

            return ReplayVerdict.valid(replay_hash)

        except ReplayVerificationError as e:
            return ReplayVerdict.invalid(e.failure)

    # ============================================================
    # LOAD TRANSCRIPT  ✅ RESTORED
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
    # VALIDATION HELPERS
    # ============================================================

    def _validate_authority(self, request, transcript):
        if transcript["authority_profile"] != request.payload["constitutional_request"]["authority_profile"]:
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.AUTHORITY_MISMATCH,
                    ReplayInvariant.ISOLATED_REPLAY_DOMAINS,
                    DivergenceLocation.AUTHORITY_BINDING,
                    "Authority mismatch",
                )
            )

    def _validate_environment(self, transcript):
        env = transcript["replay_environment"]
        if env.get("deterministic_mode") is not True or "_inference_binding" not in env:
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.ENVIRONMENT_MISMATCH,
                    ReplayInvariant.ENVIRONMENT_IDENTITY,
                    DivergenceLocation.ENVIRONMENT_VALIDATION,
                    "Invalid replay environment",
                )
            )

    def _validate_request(self, request, transcript):
        if request.canonical_hash() != transcript["request_hash"]:
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.REQUEST_MISMATCH,
                    ReplayInvariant.REQUEST_IDENTITY,
                    DivergenceLocation.REQUEST_RECONSTRUCTION,
                    "Request mismatch",
                )
            )

    def _validate_inference_binding(self, request, transcript, binding):
        if binding["input_hash"] != request.canonical_hash():
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.INFERENCE_INPUT_MISMATCH,
                    ReplayInvariant.DETERMINISTIC_INFERENCE_BINDING,
                    DivergenceLocation.INFERENCE_BINDING,
                    "Inference input mismatch",
                )
            )

    def _rerun_execution(self, request):
        h = request.canonical_hash()
        return [
            {"step": "scope_evaluation", "input_hash": h, "output_hash": _sha256(h + "scope")},
            {"step": "routing_selection", "input_hash": h, "output_hash": _sha256(h + "route")},
            {"step": "real_inference_invocation", "input_hash": h, "output_hash": _sha256(h + "inference")},
            {"step": "truth_emission", "input_hash": h, "output_hash": _sha256(h + "truth")},
        ]

    def _compare_trace(self, expected, actual):
        if expected != actual:
            raise ReplayVerificationError(
                ReplayFailure(
                    ReplayFailureMode.TRACE_DIVERGENCE,
                    ReplayInvariant.CAUSAL_RECONSTRUCTION,
                    DivergenceLocation.EXECUTION_RERUN,
                    "Trace mismatch",
                )
            )

    def _regenerate_truthpacket(self, request, trace, transcript):
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

    def _compute_replay_hash(self, truthpacket, trace):
        return _sha256(_canonical_json({"truthpacket": truthpacket, "trace": trace}))


# ============================================================
# UTILITIES
# ============================================================

def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
