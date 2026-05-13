# afritech/runtime/context/runtime_context.py

"""
Runtime Context Layer
====================

Defines the execution context for the constitutional runtime.

Responsibilities:
- Carry execution authority and payload
- Embed deterministic execution contract
- Maintain deterministic state reference
- Support audit and replay systems
- Provide strict context isolation per execution
"""

from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json

from afritech.runtime.context.deterministic_context import DeterministicContext


class RuntimeContextError(Exception):
    """Raised when context construction or validation fails"""
    pass


# -----------------------------------------------------------------
# RUNTIME CONTEXT
# -----------------------------------------------------------------

class RuntimeContext:
    """
    Canonical runtime execution context.

    RuntimeContext = Authority + Payload + ReplayRequirements
                     + DeterministicContext
    """

    def __init__(
        self,
        *,
        authority_profile: str,
        payload: Dict[str, Any],
        replay_requirements: Optional[Dict[str, Any]] = None,
        deterministic: DeterministicContext,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        if not isinstance(payload, dict):
            raise RuntimeContextError("payload must be a dict")

        if not isinstance(deterministic, DeterministicContext):
            raise RuntimeContextError(
                "deterministic must be a DeterministicContext"
            )

        self.authority_profile = authority_profile
        self.payload = payload
        self.replay_requirements = replay_requirements or {}
        self.deterministic = deterministic
        self.metadata = metadata or {}

        self.created_at = datetime.utcnow().isoformat() + "Z"

        # Deterministic identity
        self.context_hash = self._compute_context_hash()

    # -----------------------------------------------------------------
    # CANONICAL JSON
    # -----------------------------------------------------------------

    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    # -----------------------------------------------------------------
    # CONTEXT HASH (AUTHORITATIVE IDENTITY)
    # -----------------------------------------------------------------

    def _compute_context_hash(self) -> str:
        canonical = self._canonical_json({
            "authority_profile": self.authority_profile,
            "payload": self.payload,
            "replay_requirements": self.replay_requirements,
            "deterministic_hash": self.deterministic.deterministic_hash,
        })

        return hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()

    # -----------------------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Verify internal integrity of the RuntimeContext.

        Any mismatch indicates illegal mutation or construction.
        """
        return self.context_hash == self._compute_context_hash()

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "authority_profile": self.authority_profile,
            "payload": self.payload,
            "replay_requirements": self.replay_requirements,
            "deterministic": {
                "time_snapshot": self.deterministic.time_snapshot,
                "random_seed": self.deterministic.random_seed,
                "environment_hash": self.deterministic.environment_hash,
                "input_envelope_hash": self.deterministic.input_envelope_hash,
                "deterministic_hash": self.deterministic.deterministic_hash,
            },
            "metadata": self.metadata,
            "created_at": self.created_at,
            "context_hash": self.context_hash,
        }

    # -----------------------------------------------------------------
    # CONTROLLED IMMUTABILITY
    # -----------------------------------------------------------------

    def with_metadata(self, extra: Dict[str, Any]) -> "RuntimeContext":
        """
        Return a new RuntimeContext with additional metadata.

        Core execution fields remain immutable.
        """
        merged = {**self.metadata, **extra}

        return RuntimeContext(
            authority_profile=self.authority_profile,
            payload=self.payload,
            replay_requirements=self.replay_requirements,
            deterministic=self.deterministic,
            metadata=merged,
        )

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return f"<RuntimeContext hash={self.context_hash[:10]}...>"