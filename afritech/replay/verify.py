"""
afritech/replay/verify.py

Constitutional Replay Verifier (Phase‑2A Correct)

Authority:
- afritech/replay/REPLAY_VERIFIER_SPEC.md
- afritech/replay/VERIFY_INTERFACE_SPEC.md
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import hashlib
import json
import yaml


# ============================================================
# FAILURE
# ============================================================

@dataclass(frozen=True)
class ReplayFailure:
    failure_mode: str
    violated_invariant: str
    divergence_location: str
    details: str


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
            failure_mode=failure.failure_mode,
            environment_match=False,
            trace_match=False,
            truthpacket_match=False,
            violated_invariant=failure.violated_invariant,
            divergence_location=failure.divergence_location,
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
        super().__init__(failure.details)


# ============================================================
# VERIFIER
# ============================================================

class ReplayVerifier:
    """
    Deterministic constitutional replay verifier.

    Phase‑2A invariant:
    Replay artifacts are authority‑isolated.
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

            # Phase‑2A authority enforcement (first‑class)
            self._validate_authority(request, transcript)

            # Phase‑1 invariants
            self._validate_environment(transcript)
            self._validate_request(request, transcript)

            # Deterministic execution rerun
            rerun_trace = self._rerun_execution(request)
            self._compare_trace(
                transcript["execution_trace"],
                rerun_trace,
            )

            # TruthPacket regeneration
            truthpacket = self._regenerate_truthpacket(
                request,
                rerun_trace,
            )

            truthpacket_hash = _sha256(
                _canonical_json(truthpacket)
            )

            if truthpacket_hash != transcript["truth_packet_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        failure_mode="truthpacket_divergence",
                        violated_invariant="truthpacket_identity",
                        divergence_location="truthpacket_regeneration",
                        details="TruthPacket hash mismatch",
                    )
                )

            replay_hash = self._compute_replay_hash(
                truthpacket,
                rerun_trace,
            )

            if replay_hash != transcript["replay_hash"]:
                raise ReplayVerificationError(
                    ReplayFailure(
                        failure_mode="hash_mismatch",
                        violated_invariant="deterministic_identity",
                        divergence_location="hash_recomputation",
                        details="Replay hash mismatch",
                    )
                )

            return ReplayVerdict.valid(replay_hash)

        except ReplayVerificationError as e:
            return ReplayVerdict.invalid(e.failure)


    # ============================================================
    # AUTHORITY (PHASE‑2A ENFORCEMENT SURFACE)
    # ============================================================

    def _validate_authority(
        self,
        request: ConstitutionalRequest,
        transcript: dict[str, Any],
    ) -> None:

        request_authority = (
            request.payload["constitutional_request"]["authority_profile"]
        )

        transcript_authority = transcript.get("authority_profile")

        if transcript_authority is None:
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="missing_authority_binding",
                    violated_invariant="authority_identity",
                    divergence_location="authority_binding",
                    details="Transcript missing authority_profile",
                )
            )

        if request_authority != transcript_authority:
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="authority_mismatch",
                    violated_invariant="isolated_replay_domains",
                    divergence_location="authority_binding",
                    details="Authority mismatch between request and transcript",
                )
            )


    # ============================================================
    # LOAD TRANSCRIPT
    # ============================================================

    def _load_transcript(self, path: str) -> dict[str, Any]:
        p = Path(path)

        if not p.exists() or not p.is_file():
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="invalid_transcript_path",
                    violated_invariant="transcript_existence",
                    divergence_location="transcript_load",
                    details="Transcript file not found",
                )
            )

        with p.open("r", encoding="utf-8") as f:
            transcript = yaml.safe_load(f)

        required_fields = {
            "authority_profile",
            "request_hash",
            "replay_environment",
            "execution_trace",
            "truth_packet_hash",
            "replay_hash",
        }

        if not isinstance(transcript, dict) or not required_fields.issubset(transcript):
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="invalid_transcript_schema",
                    violated_invariant="transcript_integrity",
                    divergence_location="transcript_load",
                    details="Missing transcript fields",
                )
            )

        return transcript


    # ============================================================
    # ENVIRONMENT
    # ============================================================

    def _validate_environment(self, transcript: dict[str, Any]) -> None:
        env = transcript["replay_environment"]

        required_fields = {
            "runtime_version",
            "model_version",
            "constitution_version",
            "deterministic_mode",
        }

        if not required_fields.issubset(env):
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="environment_mismatch",
                    violated_invariant="environment_identity",
                    divergence_location="environment_validation",
                    details="Missing replay environment fields",
                )
            )

        if env["deterministic_mode"] is not True:
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="environment_mismatch",
                    violated_invariant="deterministic_environment",
                    divergence_location="environment_validation",
                    details="Deterministic mode required",
                )
            )


    # ============================================================
    # REQUEST
    # ============================================================

    def _validate_request(
        self,
        request: ConstitutionalRequest,
        transcript: dict[str, Any],
    ) -> None:

        if request.canonical_hash() != transcript["request_hash"]:
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="request_mismatch",
                    violated_invariant="request_identity",
                    divergence_location="request_reconstruction",
                    details="Request hash mismatch",
                )
            )


    # ============================================================
    # EXECUTION RERUN (DETERMINISTIC)
    # ============================================================

    def _rerun_execution(
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
                "step": "truth_emission",
                "input_hash": h,
                "output_hash": _sha256(h + "truth"),
            },
        ]


    # ============================================================
    # TRACE
    # ============================================================

    def _compare_trace(
        self,
        expected: list[dict[str, str]],
        actual: list[dict[str, str]],
    ) -> None:

        if expected != actual:
            raise ReplayVerificationError(
                ReplayFailure(
                    failure_mode="trace_divergence",
                    violated_invariant="causal_reconstruction",
                    divergence_location="execution_rerun",
                    details="Execution trace mismatch",
                )
            )


    # ============================================================
    # TRUTHPACKET
    # ============================================================

    def _regenerate_truthpacket(
        self,
        request: ConstitutionalRequest,
        trace: list[dict[str, str]],
    ) -> dict[str, Any]:

        authority_profile = (
            request.payload["constitutional_request"]["authority_profile"]
        )

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


    # ============================================================
    # REPLAY HASH
    # ============================================================

    def _compute_replay_hash(
        self,
        truthpacket: dict[str, Any],
        trace: list[dict[str, str]],
    ) -> str:

        return _sha256(
            _canonical_json(
                {
                    "truthpacket": truthpacket,
                    "trace": trace,
                }
            )
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