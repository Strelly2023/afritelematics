"""
afritech/replay/failures.py

Canonical replay failure definitions.

Purpose:
- Centralize replay failure modes
- Enforce typed, invariant-referenced replay refusal
- Eliminate ad-hoc failure strings in verifier logic

Authority:
- afritech/replay/REPLAY_VERIFIER_SPEC.md
- afritech/replay/VERIFY_INTERFACE_SPEC.md
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ============================================================
# FAILURE MODES (CANONICAL)
# ============================================================

class ReplayFailureMode(str, Enum):
    """
    Canonical replay failure mode identifiers.
    """

    # -----------------------
    # Transcript / I/O
    # -----------------------
    INVALID_TRANSCRIPT_PATH = "invalid_transcript_path"
    INVALID_TRANSCRIPT_SCHEMA = "invalid_transcript_schema"
    MISSING_TRANSCRIPT_FIELD = "missing_transcript_field"

    # -----------------------
    # Authority (Phase‑2A)
    # -----------------------
    MISSING_AUTHORITY_BINDING = "missing_authority_binding"
    AUTHORITY_MISMATCH = "authority_mismatch"

    # -----------------------
    # Environment
    # -----------------------
    ENVIRONMENT_MISMATCH = "environment_mismatch"

    # -----------------------
    # Request / Trace
    # -----------------------
    REQUEST_MISMATCH = "request_mismatch"
    TRACE_DIVERGENCE = "trace_divergence"

    # -----------------------
    # TruthPacket / Replay
    # -----------------------
    TRUTHPACKET_DIVERGENCE = "truthpacket_divergence"
    HASH_MISMATCH = "hash_mismatch"

    # -----------------------
    # Inference Binding (Phase‑2B)
    # -----------------------
    MISSING_INFERENCE_BINDING = "missing_inference_binding"
    INFERENCE_INPUT_MISMATCH = "inference_input_mismatch"
    MODEL_IDENTITY_MISMATCH = "model_identity_mismatch"
    NONDETERMINISTIC_INFERENCE = "nondeterministic_inference"


# ============================================================
# VIOLATED INVARIANTS (CANONICAL)
# ============================================================

class ReplayInvariant(str, Enum):
    """
    Canonical replay invariants that may be violated.
    """

    # ----------------------------------------------------
    # Phase‑1 Invariants
    # ----------------------------------------------------
    TRANSCRIPT_EXISTENCE = "transcript_existence"
    TRANSCRIPT_INTEGRITY = "transcript_integrity"
    REQUEST_IDENTITY = "request_identity"
    DETERMINISTIC_IDENTITY = "deterministic_identity"
    TRUTHPACKET_IDENTITY = "truthpacket_identity"
    CAUSAL_RECONSTRUCTION = "causal_reconstruction"

    # ----------------------------------------------------
    # Phase‑2A Invariants
    # ----------------------------------------------------
    AUTHORITY_IDENTITY = "authority_identity"
    ISOLATED_REPLAY_DOMAINS = "isolated_replay_domains"

    # ----------------------------------------------------
    # Environment Invariants
    # ----------------------------------------------------
    ENVIRONMENT_IDENTITY = "environment_identity"
    DETERMINISTIC_INFERENCE = "deterministic_inference"

    # ----------------------------------------------------
    # Phase‑2B Invariants
    # ----------------------------------------------------
    INFERENCE_BINDING_REQUIRED = "inference_binding_required"
    DETERMINISTIC_INFERENCE_BINDING = "deterministic_inference_binding"
    MODEL_IDENTITY = "model_identity"


# ============================================================
# DIVERGENCE LOCATIONS (CANONICAL)
# ============================================================

class DivergenceLocation(str, Enum):
    """
    Canonical locations where replay divergence can occur.
    """

    TRANSCRIPT_LOAD = "transcript_load"
    TRANSCRIPT_SCHEMA = "transcript_schema"
    AUTHORITY_BINDING = "authority_binding"
    ENVIRONMENT_VALIDATION = "environment_validation"
    REQUEST_RECONSTRUCTION = "request_reconstruction"
    EXECUTION_RERUN = "execution_rerun"
    TRUTHPACKET_REGENERATION = "truthpacket_regeneration"
    HASH_RECOMPUTATION = "hash_recomputation"
    INFERENCE_BINDING = "inference_binding"


# ============================================================
# FAILURE OBJECT
# ============================================================

@dataclass(frozen=True)
class ReplayFailure:
    """
    Structured replay failure.

    Emitted exclusively by the replay verifier and
    consumed by:
    - CLI output
    - audit export
    - CI enforcement
    """

    failure_mode: ReplayFailureMode
    violated_invariant: ReplayInvariant
    divergence_location: DivergenceLocation
    details: Optional[str] = None

    def as_dict(self) -> dict[str, str]:
        """
        Serialize failure into a stable, machine‑readable form.
        """
        return {
            "failure_mode": self.failure_mode.value,
            "violated_invariant": self.violated_invariant.value,
            "divergence_location": self.divergence_location.value,
            "details": self.details or "",
        }
