"""Canonical worker result types for deterministic distributed execution."""

from __future__ import annotations

from typing import Any, Dict, Optional
from dataclasses import dataclass, field
import json
import hashlib
#afritech/execution/worker/types.py

@dataclass(frozen=True)
class WorkerResult:
    """
    Canonical execution result for all worker outputs.

    HARD GUARANTEES:
    - Deterministic serialization
    - Replay-safe hashing
    - Immutable (frozen)
    - Complete execution boundary

    This is the ONLY admissible worker output type.
    """

    # ---------------------------------------------------------
    # CORE IDENTITY
    # ---------------------------------------------------------
    request_id: str
    partition_id: Optional[str | int]


    # ---------------------------------------------------------
    # EXECUTION OUTPUT
    # ---------------------------------------------------------
    outputs: Dict[str, Any]

    # ---------------------------------------------------------
    # TRACE (REPLAY + OBSERVABILITY)
    # ---------------------------------------------------------
    trace: Dict[str, Any]

    # ---------------------------------------------------------
    # DETERMINISTIC HASH
    # ---------------------------------------------------------
    replay_hash: str

    # ---------------------------------------------------------
    # INTERNAL CACHE (not part of identity)
    # ---------------------------------------------------------
    _cached_serialized: Optional[str] = field(default=None, init=False, repr=False)

    # ---------------------------------------------------------
    # POST INIT VALIDATION
    # ---------------------------------------------------------

    def __post_init__(self) -> None:
        """
        Enforce strict structural validity.
        """
        if not isinstance(self.request_id, str):
            raise TypeError("request_id must be string")

        if self.partition_id is not None and not isinstance(self.partition_id, (int, str)):
            raise TypeError("partition_id must be int, str, or None")

        if not isinstance(self.outputs, dict):
            raise TypeError("outputs must be dict")

        if not isinstance(self.trace, dict):
            raise TypeError("trace must be dict")

        if not isinstance(self.replay_hash, str):
            raise TypeError("replay_hash must be string")

    # ---------------------------------------------------------
    # DETERMINISTIC SERIALIZATION
    # ---------------------------------------------------------

    def serialize(self) -> str:
        """
        Deterministic serialization for hashing & comparison.

        MUST:
        - sort keys
        - eliminate non-deterministic structures
        """
        if self._cached_serialized is not None:
            return self._cached_serialized

        canonical_dict = {
            "request_id": self.request_id,
            "partition_id": self.partition_id,
            "outputs": self.outputs,
            "trace": self.trace,
            "replay_hash": self.replay_hash,
        }

        serialized = json.dumps(
            canonical_dict,
            sort_keys=True,
            separators=(",", ":"),  # remove whitespace
        )

        object.__setattr__(self, "_cached_serialized", serialized)
        return serialized

    # ---------------------------------------------------------
    # HASH (SECONDARY VERIFICATION)
    # ---------------------------------------------------------

    def compute_canonical_hash(self) -> str:
        """
        Compute deterministic hash of entire result object.

        Used for:
        - distributed comparison
        - replay validator
        """
        serialized = self.serialize()
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    # ---------------------------------------------------------
    # EQUALITY (STRICT)
    # ---------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        """
        Strict equality:
        - replay_hash must match
        - serialized structure must match
        """
        if isinstance(other, str):
            return self.replay_hash == other

        if not isinstance(other, WorkerResult):
            return False

        # Fast path
        if self.replay_hash != other.replay_hash:
            return False

        # Deep deterministic comparison
        return self.serialize() == other.serialize()

    # ---------------------------------------------------------
    # REPLAY EQUIVALENCE (EXPLICIT API)
    # ---------------------------------------------------------

    def is_replay_equivalent(self, other: WorkerResult) -> bool:
        """
        Explicit replay equivalence check.

        THIS is what distributed replay validator should use.
        """
        return self == other

    # ---------------------------------------------------------
    # DEBUG / INSPECTION
    # ---------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Debug-friendly view (non-canonical use only).
        """
        return {
            "request_id": self.request_id,
            "partition_id": self.partition_id,
            "outputs": self.outputs,
            "trace": self.trace,
            "replay_hash": self.replay_hash,
        }

    # ---------------------------------------------------------
    # FACTORY (SAFE CONSTRUCTION)
    # ---------------------------------------------------------

    @classmethod
    def create(
        cls,
        request_id: str,
        partition_id: Optional[int],
        outputs: Dict[str, Any],
        trace: Dict[str, Any],
    ) -> WorkerResult:
        """
        Safe constructor that enforces canonical hash generation.
        """

        # Deterministic output hash
        output_serialized = json.dumps(
            outputs,
            sort_keys=True,
            separators=(",", ":"),
        )

        replay_hash = hashlib.sha256(output_serialized.encode("utf-8")).hexdigest()

        return cls(
            request_id=request_id,
            partition_id=partition_id,
            outputs=outputs,
            trace=trace,
            replay_hash=replay_hash,
        )
