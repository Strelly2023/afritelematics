# afritech/replay/verify.py

"""
AfriTech Constitutional Replay Verifier
=======================================

Deterministic replay verification system.

Replay is:
- verification
- reconstruction
- admissibility validation

Replay is NOT:
- execution
- mutation
- runtime admission
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
            failure_mode=failure.failure_mode.value,
            environment_match=(
                failure.failure_mode
                != ReplayFailureMode.ENVIRONMENT_MISMATCH
            ),
            trace_match=(
                failure.failure_mode
                != ReplayFailureMode.TRACE_DIVERGENCE
            ),
            truthpacket_match=(
                failure.failure_mode
                != ReplayFailureMode.TRUTHPACKET_DIVERGENCE
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

    def __init__(
        self,
        failure: ReplayFailure,
    ):

        self.failure = failure

        super().__init__(
            failure.details or ""
        )


# ============================================================
# VERIFIER
# ============================================================

class ReplayVerifier:

    # ========================================================
    # PUBLIC
    # ========================================================

    def verify(
        self,
        *,
        transcript_path: str,
        request: ConstitutionalRequest,
    ) -> ReplayVerdict:

        try:

            transcript = self._load_transcript(
                transcript_path
            )

            self._verify_registry()

            self._verify_environment(
                transcript
            )

            self._verify_request(
                request,
                transcript,
            )

            recomputed_trace = (
                self._rerun_execution(
                    request
                )
            )

            self._verify_trace(
                recomputed_trace,
                transcript,
            )

            regenerated_truthpacket = (
                self._regenerate_truthpacket(
                    request=request,
                    trace=recomputed_trace,
                    transcript=transcript,
                )
            )

            self._verify_truthpacket(
                regenerated_truthpacket,
                transcript,
            )

            replay_hash = (
                self._compute_replay_hash(
                    regenerated_truthpacket,
                    recomputed_trace,
                )
            )

            self._verify_replay_hash(
                replay_hash,
                transcript,
            )

            return ReplayVerdict.valid(
                replay_hash
            )

        except ReplayVerificationError as e:

            return ReplayVerdict.invalid(
                e.failure
            )

    # ========================================================
    # REGISTRY
    # ========================================================

    def _verify_registry(self):

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
                    .REGISTRY_ATTESTATION,

                    "Registry not sealed",
                )
            )

    # ========================================================
    # ENVIRONMENT
    # ========================================================

    def _verify_environment(
        self,
        transcript,
    ):

        env = transcript.get(
            "replay_environment",
            {},
        )

        if not env.get(
            "deterministic_mode",
            False,
        ):

            raise ReplayVerificationError(

                ReplayFailure(

                    ReplayFailureMode
                    .ENVIRONMENT_MISMATCH,

                    ReplayInvariant
                    .ENVIRONMENT_IDENTITY,

                    DivergenceLocation
                    .REGISTRY_ATTESTATION,

                    "Deterministic mode disabled",
                )
            )

    # ========================================================
    # REQUEST
    # ========================================================

    def _verify_request(
        self,
        request,
        transcript,
    ):

        expected = transcript.get(
            "request_hash"
        )

        actual = request.canonical_hash()

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
    # TRACE
    # ========================================================

    def _verify_trace(
        self,
        recomputed_trace,
        transcript,
    ):

        expected = transcript.get(
            "execution_trace"
        )

        if recomputed_trace != expected:

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
    # TRUTHPACKET
    # ========================================================

    def _verify_truthpacket(
        self,
        truthpacket,
        transcript,
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
    # HASH
    # ========================================================

    def _verify_replay_hash(
        self,
        replay_hash,
        transcript,
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
    # LOAD
    # ========================================================

    def _load_transcript(
        self,
        path: str,
    ):

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

                    "Transcript missing",
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

                    "Transcript invalid",
                )
            )

        return transcript

    # ========================================================
    # DETERMINISTIC RECONSTRUCTION
    # ========================================================

    def _rerun_execution(
        self,
        request,
    ):

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
    # TRUTHPACKET
    # ========================================================

    def _regenerate_truthpacket(
        self,
        *,
        request,
        trace,
        transcript,
    ):

        env = transcript[
            "replay_environment"
        ]

        return {

            "claims": [
                "deterministic constitutional execution"
            ],

            "authority_profile":
                transcript.get(
                    "authority_profile",
                    "UNKNOWN_AUTHORITY",
                ),

            "inference_binding":
                env.get(
                    "_inference_binding",
                    "UNKNOWN_BINDING",
                ),

            "provenance_chain":
                trace,

            "epoch_id":
                request.payload[
                    "constitutional_request"
                ][
                    "epoch_id"
                ],
        }

    # ========================================================
    # HASH
    # ========================================================

    def _compute_replay_hash(
        self,
        truthpacket,
        trace,
    ):

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