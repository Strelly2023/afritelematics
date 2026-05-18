from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ReplayFailureMode(str, Enum):
    ENVIRONMENT_MISMATCH = "environment_mismatch"
    REQUEST_MISMATCH = "request_mismatch"
    TRACE_DIVERGENCE = "trace_divergence"
    TRUTHPACKET_DIVERGENCE = "truthpacket_divergence"
    HASH_MISMATCH = "hash_mismatch"
    INVALID_TRANSCRIPT_PATH = "invalid_transcript_path"
    INVALID_TRANSCRIPT_SCHEMA = "invalid_transcript_schema"


class ReplayInvariant(str, Enum):
    ENVIRONMENT_IDENTITY = "environment_identity"
    REQUEST_IDENTITY = "request_identity"
    CAUSAL_RECONSTRUCTION = "causal_reconstruction"
    TRUTHPACKET_IDENTITY = "truthpacket_identity"
    DETERMINISTIC_IDENTITY = "deterministic_identity"
    TRANSCRIPT_EXISTENCE = "transcript_existence"
    TRANSCRIPT_INTEGRITY = "transcript_integrity"


class DivergenceLocation(str, Enum):
    REGISTRY_ATTESTATION = "registry_attestation"
    REQUEST_RECONSTRUCTION = "request_reconstruction"
    EXECUTION_RERUN = "execution_rerun"
    TRUTHPACKET_REGENERATION = "truthpacket_regeneration"
    HASH_RECOMPUTATION = "hash_recomputation"
    TRANSCRIPT_LOAD = "transcript_load"
    TRANSCRIPT_SCHEMA = "transcript_schema"


@dataclass(frozen=True)
class ReplayFailure:
    failure_mode: ReplayFailureMode
    violated_invariant: ReplayInvariant
    divergence_location: DivergenceLocation
    details: str = ""
