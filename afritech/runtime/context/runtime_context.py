"""
afritech/runtime/context/runtime_context.py

Runtime Context Layer
====================

Defines the execution context for the constitutional runtime.

Responsibilities:
- Carry execution metadata
- Maintain deterministic state reference
- Support audit and replay systems
- Provide context isolation per execution
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib
import json


class RuntimeContextError(Exception):
    """Raised when context construction or validation fails"""
    pass


# -----------------------------------------------------------------
# RUNTIME CONTEXT
# -----------------------------------------------------------------

class RuntimeContext:

    def __init__(
        self,
        authority_profile: str,
        payload: Dict[str, Any],
        replay_requirements: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Core execution context

        :param authority_profile: RBAC or governance authority
        :param payload: execution input
        :param replay_requirements: replay/determinism constraints
        :param metadata: optional execution metadata
        """

        if not isinstance(payload, dict):
            raise RuntimeContextError("payload must be a dict")

        self.authority_profile = authority_profile
        self.payload = payload
        self.replay_requirements = replay_requirements or {}
        self.metadata = metadata or {}

        self.created_at = datetime.utcnow().isoformat() + "Z"

        # Deterministic identity
        self.context_hash = self._compute_hash()

    # -----------------------------------------------------------------
    # HASH (DETERMINISTIC IDENTITY)
    # -----------------------------------------------------------------

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":")
        )

    def _compute_hash(self) -> str:
        canonical = self._canonical_json({
            "authority": self.authority_profile,
            "payload": self.payload,
            "replay_requirements": self.replay_requirements,
        })

        return hashlib.sha256(canonical.encode()).hexdigest()

    # -----------------------------------------------------------------
    # EXPORT
    # -----------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "authority_profile": self.authority_profile,
            "payload": self.payload,
            "replay_requirements": self.replay_requirements,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "context_hash": self.context_hash,
        }

    # -----------------------------------------------------------------
    # VALIDATION
    # -----------------------------------------------------------------

    def verify(self) -> bool:
        """
        Ensure context integrity
        """
        recomputed = self._compute_hash()
        return recomputed == self.context_hash

    # -----------------------------------------------------------------
    # MUTATION (CONTROLLED)
    # -----------------------------------------------------------------

    def with_metadata(self, extra: Dict[str, Any]) -> "RuntimeContext":
        """
        Return new context with additional metadata (immutable pattern)
        """
        merged = {**self.metadata, **extra}

        return RuntimeContext(
            authority_profile=self.authority_profile,
            payload=self.payload,
            replay_requirements=self.replay_requirements,
            metadata=merged,
        )

    # -----------------------------------------------------------------
    # STRING REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self):
        return f"<RuntimeContext hash={self.context_hash[:10]}...>"


# -----------------------------------------------------------------
# FACTORY FUNCTION (HELPER)
# -----------------------------------------------------------------

def build_runtime_context(request: Dict[str, Any]) -> RuntimeContext:
    """
    Build context from API request format
    """

    if not isinstance(request, dict):
        raise RuntimeContextError("request must be dict")

    return RuntimeContext(
        authority_profile=request.get("authority_profile", "unknown"),
        payload=request.get("payload", {}),
        replay_requirements=request.get("replay_requirements", {}),
        metadata={
            "source": "api",
        },
    )