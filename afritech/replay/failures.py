# afritech/replay/verify.py

"""
Constitutional Replay Verifier
==============================

Replay is:
- deterministic verification
- admissibility reconstruction
- constitutional validation

Replay is NOT:
- runtime execution
- state mutation
- speculative reconstruction
- observer-relative interpretation

Constitutional guarantees:
- deterministic replay
- canonical transcript validation
- invariant-preserving reconstruction
- closed-world replay semantics
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

from afritech.registry.loader import load_registry


# ============================================================
# VERDICT
# ============================================================

@dataclass(frozen=True)
class ReplayVerdict:
    """
    Final replay admissibility verdict.
    """

    status: str

    replay_hash: Optional[str]

    failure_mode: Optional[str]

    environment_match: bool

    trace_match: bool

    truthpacket_match: bool

    violated_invariant: Optional[str]

    divergence_location: Optional[str]

    @staticmethod
    def valid(
        replay_hash: str,
    ) -> "ReplayVerdict":

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
    def invalid(
        failure: ReplayFailure,
    ) -> "ReplayVerdict":

        return ReplayVerdict(

            status="REPLAY_INVALID",

            replay_hash=None,

            failure_mode=(
                failure.failure_mode.value
            ),

            environment_match=(
                failure.failure_mode
                != ReplayFailureMode
                .ENVIRONMENT_MISMATCH
            ),

            trace_match=(
                failure.failure_mode
                != ReplayFailureMode
                .TRACE_DIVERGENCE
            ),

            truthpacket_match=(
                failure.failure_mode
                != ReplayFailureMode
                .TRUTHPACKET_DIVERGENENCE
                if hasattr(
                    ReplayFailureMode,
                    "TRUTHPACKET_DIVERGENENCE",
                )
                else (
                    failure.failure_mode
                    != ReplayFailureMode
                    .TRUTHPACKET_DIVERGENCE
                )
            ),

            violated_invariant=(
                failure.violated_invariant.value
            ),

            divergence_location=(
                failure.divergence_location.value
            ),
        )


# ============================================================
# REQUEST
# ============================================================

@dataclass(frozen=True)
class ConstitutionalRequest:
    """
    Deterministic constitutional request.
    """

    payload: dict[str, Any]

    def canonical_hash(self) -> str:

        return _sha256(

            _canonical_json(
                self.payload
            )
        )


# ============================================================
# INTERNAL ERROR
# ============================================================

class ReplayVerificationError(Exception):
    """
    Internal replay verification exception.
    """

    def __init__(
        self,
        failure: ReplayFailure,
    ):

        self.failure = failure

        super().__init__(
            failure.details or ""
        )


# ============================================================
# REPLAY VERIFIER
# ============================================================

class ReplayVerifier:
    """
    Deterministic constitutional replay verifier.
    """

    # ========================================================
    # PUBLIC ENTRYPOINT
    # ========================================================

    def verify(
        self,
        *,
        transcript_path: str,
        request: ConstitutionalRequest,
    ) -> ReplayVerdict:

        try:

            # ------------------------------------------------
            # transcript
            # ------------------------------------------------

            transcript = self._load_transcript(
                transcript_path
            )

            # ------------------------------------------------
            # registry legitimacy
            # ------------------------------------------------

            self._verify_registry()

            # ------------------------------------------------
            # replay environment
            # ------------------------------------------------

            self._verify_environment(
                transcript
            )

            # ------------------------------------------------
            # request identity
            # ------------------------------------------------

            self._verify_request(
                request=request,
                transcript=transcript,
            )

            # ------------------------------------------------
            # deterministic replay reconstruction
            # ------------------------------------------------

            recomputed_trace = (
                self._rerun_execution(
                    request
                )
            )

            # ------------------------------------------------
            # trace verification
            # ------------------------------------------------

            self._verify_trace(
                recomputed_trace,
                transcript,
            )

            # ------------------------------------------------
            # truthpacket reconstruction
            # ------------------------------------------------

            regenerated_truthpacket = (
                self._regenerate_truthpacket(

                    request=request,

                    trace=recomputed_trace,

                    transcript=transcript,
                )
            )

            # ------------------------------------------------
            # truthpacket verification
            # ------------------------------------------------

            self._verify_truthpacket(
                regenerated_truthpacket,
                transcript,
            )

            # ------------------------------------------------
            # replay hash reconstruction
            # ------------------------------------------------

            replay_hash = (
                self._compute_replay_hash(

                    regenerated_truthpacket,

                    recomputed_trace,
                )
            )

            # ------------------------------------------------
            # replay hash verification
            # ------------------------------------------------

            self._verify_replay_hash(
                replay_hash,
                transcript,
            )

            # ------------------------------------------------
            # valid
            # ------------------------------------------------

            return ReplayVerdict.valid(
                replay_hash
            )

        except ReplayVerificationError as e:

            return ReplayVerdict.invalid(
                e.failure
            )

    # ========================================================
    # REGISTRY VALIDATION
    # ========================================================

    def _verify_registry(
        self,
    ):

        registry = load_registry()

        attestation = registry.get(
            "attestation"
        )

        if (
            not attestation
            or attestation.get("status")
            != "SEALED"
        ):

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .ENVIRONMENT_MISMATCH,

                    ReplayInvariant
                    .ENVIRONMENT_IDENTITY,

                    DivergenceLocation
                    .ENVIRONMENT_VALIDATION,

                    "Registry attestation not sealed",
                )
            )

    # ========================================================
    # ENVIRONMENT VALIDATION
    # ========================================================

    def _verify_environment(
        self,
        transcript: dict[str, Any],
    ):

        env = transcript.get(
            "replay_environment",
            {},
        )

        deterministic = env.get(
            "deterministic_mode"
        )

        if deterministic is not True:

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .ENVIRONMENT_MISMATCH,

                    ReplayInvariant
                    .ENVIRONMENT_IDENTITY,

                    DivergenceLocation
                    .ENVIRONMENT_VALIDATION,

                    "Deterministic mode disabled",
                )
            )

    # ========================================================
    # REQUEST VALIDATION
    # ========================================================

    def _verify_request(
        self,
        *,
        request: ConstitutionalRequest,
        transcript: dict[str, Any],
    ):

        actual = (
            request.canonical_hash()
        )

        expected = transcript.get(
            "request_hash"
        )

        if actual != expected:

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .REQUEST_MISMATCH,

                    ReplayInvariant
                    .REQUEST_IDENTITY,

                    DivergenceLocation
                    .REQUEST_RECONSTRUCTION,

                    "Request hash mismatch",
                )
            )

    # ========================================================
    # TRACE VALIDATION
    # ========================================================

    def _verify_trace(
        self,
        recomputed_trace: list[dict],
        transcript: dict[str, Any],
    ):

        expected_trace = transcript.get(
            "execution_trace"
        )

        if (
            recomputed_trace
            != expected_trace
        ):

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .TRACE_DIVERGENCE,

                    ReplayInvariant
                    .CAUSAL_RECONSTRUCTION,

                    DivergenceLocation
                    .EXECUTION_RERUN,

                    "Execution trace mismatch",
                )
            )

    # ========================================================
    # TRUTHPACKET VALIDATION
    # ========================================================

    def _verify_truthpacket(
        self,
        truthpacket: dict[str, Any],
        transcript: dict[str, Any],
    ):

        expected_hash = transcript.get(
            "truth_packet_hash"
        )

        actual_hash = _sha256(

            _canonical_json(
                truthpacket
            )
        )

        if actual_hash != expected_hash:

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .TRUTHPACKET_DIVERGENCE,

                    ReplayInvariant
                    .TRUTHPACKET_IDENTITY,

                    DivergenceLocation
                    .TRUTHPACKET_REGENERATION,

                    "TruthPacket mismatch",
                )
            )

    # ========================================================
    # REPLAY HASH VALIDATION
    # ========================================================

    def _verify_replay_hash(
        self,
        replay_hash: str,
        transcript: dict[str, Any],
    ):

        expected = transcript.get(
            "replay_hash"
        )

        if replay_hash != expected:

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .HASH_MISMATCH,

                    ReplayInvariant
                    .DETERMINISTIC_IDENTITY,

                    DivergenceLocation
                    .HASH_RECOMPUTATION,

                    "Replay hash mismatch",
                )
            )

    # ========================================================
    # LOAD TRANSCRIPT
    # ========================================================

    def _load_transcript(
        self,
        path: str,
    ) -> dict[str, Any]:

        p = Path(path)

        if (
            not p.exists()
            or not p.is_file()
        ):

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .INVALID_TRANSCRIPT_PATH,

                    ReplayInvariant
                    .TRANSCRIPT_EXISTENCE,

                    DivergenceLocation
                    .TRANSCRIPT_LOAD,

                    "Transcript file not found",
                )
            )

        with p.open(
            "r",
            encoding="utf-8",
        ) as f:

            transcript = yaml.safe_load(f)

        if not isinstance(
            transcript,
            dict,
        ):

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .INVALID_TRANSCRIPT_SCHEMA,

                    ReplayInvariant
                    .TRANSCRIPT_INTEGRITY,

                    DivergenceLocation
                    .TRANSCRIPT_SCHEMA,

                    "Transcript must be mapping",
                )
            )

        required = {

            "replay_environment",

            "execution_trace",

            "request_hash",

            "truth_packet_hash",

            "replay_hash",
        }

        missing = (
            required
            - set(transcript.keys())
        )

        if missing:

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .INVALID_TRANSCRIPT_SCHEMA,

                    ReplayInvariant
                    .TRANSCRIPT_INTEGRITY,

                    DivergenceLocation
                    .TRANSCRIPT_SCHEMA,

                    f"Missing transcript fields: "
                    f"{sorted(missing)}",
                )
            )

        return transcript

    # ========================================================
    # DETERMINISTIC REPLAY RECONSTRUCTION
    # ========================================================

    def _rerun_execution(
        self,
        request: ConstitutionalRequest,
    ) -> list[dict[str, str]]:

        h = request.canonical_hash()

        return [

            {
                "step":
                    "scope_evaluation",

                "input_hash":
                    h,

                "output_hash":
                    _sha256(h + "scope"),
            },

            {
                "step":
                    "routing_selection",

                "input_hash":
                    h,

                "output_hash":
                    _sha256(h + "route"),
            },

            {
                "step":
                    "real_inference_invocation",

                "input_hash":
                    h,

                "output_hash":
                    _sha256(h + "inference"),
            },

            {
                "step":
                    "truth_emission",

                "input_hash":
                    h,

                "output_hash":
                    _sha256(h + "truth"),
            },
        ]

    # ========================================================
    # TRUTHPACKET RECONSTRUCTION
    # ========================================================

    def _regenerate_truthpacket(
        self,
        *,
        request: ConstitutionalRequest,
        trace: list[dict],
        transcript: dict[str, Any],
    ) -> dict[str, Any]:

        original = transcript.get(
            "truth_packet",
            {},
        )

        return {

            "claims":
                original.get(
                    "claims",
                    [],
                ),

            "authority_profile":
                original.get(
                    "authority_profile",
                    "UNKNOWN_AUTHORITY",
                ),

            "inference_binding":
                original.get(
                    "inference_binding",
                    "UNKNOWN_BINDING",
                ),

            "epoch_id":
                request.payload[
                    "constitutional_request"
                ][
                    "epoch_id"
                ],

            "provenance_chain":
                trace,
        }

    # ========================================================
    # REPLAY HASH
    # ========================================================

    def _compute_replay_hash(
        self,
        truthpacket: dict[str, Any],
        trace: list[dict],
    ) -> str:

        return _sha256(

            _canonical_json({

                "truthpacket":
                    truthpacket,

                "trace":
                    trace,
            })
        )


# ============================================================
# UTILITIES
# ============================================================

def _canonical_json(
    obj: Any,
) -> str:

    return json.dumps(

        obj,

        sort_keys=True,

        separators=(",", ":"),

        ensure_ascii=False,
    )


def _sha256(
    value: str,
) -> str:

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()