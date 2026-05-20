# afritech/runtime/context/runtime_context.py

"""
Runtime Context Compatibility Layer
==================================

Canonical RuntimeContext now lives in:

    afritech.shared.context

This module exists ONLY as a compatibility bridge for
legacy runtime imports.

Constitutional guarantees:

- single canonical RuntimeContext definition
- replay-safe deterministic hashing
- immutable execution topology
- backward-compatible runtime imports
- no duplicate context semantics
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from afritech.shared.context import (
    RuntimeContext as SharedRuntimeContext,
)

from afritech.core.runtime.context.deterministic_context import (
    DeterministicContext,
)


# ============================================================
# ERRORS
# ============================================================

class RuntimeContextError(
    Exception
):
    """
    Runtime context construction failure.
    """
    pass


# ============================================================
# CANONICAL RUNTIME CONTEXT
# ============================================================

class RuntimeContext(
    SharedRuntimeContext
):
    """
    Backward-compatible runtime wrapper.

    Preserves older runtime constructor semantics while
    delegating canonical execution identity to:

        afritech.shared.context.RuntimeContext
    """

    def __init__(
        self,
        *,
        authority_profile: str,
        payload: Dict[str, Any],
        replay_requirements: Optional[
            Dict[str, Any]
        ] = None,
        deterministic: Optional[
            DeterministicContext
        ] = None,
        metadata: Optional[
            Dict[str, Any]
        ] = None,
        timestamp: str | None = None,
        context_hash: str = "",
    ):

        # ----------------------------------------------------
        # structural validation
        # ----------------------------------------------------

        if not isinstance(
            payload,
            dict,
        ):

            raise RuntimeContextError(
                "payload must be dict"
            )

        if (
            deterministic is not None
            and not isinstance(
                deterministic,
                DeterministicContext,
            )
        ):

            raise RuntimeContextError(
                "deterministic must be "
                "DeterministicContext"
            )

        # ----------------------------------------------------
        # canonical shared initialization
        # ----------------------------------------------------

        super().__init__(

            authority_profile=
                authority_profile,

            payload=
                payload,

            replay_requirements=
                replay_requirements
                or {},

            timestamp=
                timestamp,

            context_hash=
                context_hash,
        )

        # ----------------------------------------------------
        # runtime-only compatibility fields
        # ----------------------------------------------------

        self.deterministic = (
            deterministic
        )

        self.metadata = (
            metadata
            or {}
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        base = super().to_dict()

        if self.deterministic:

            base[
                "deterministic"
            ] = {

                "time_snapshot":
                    self.deterministic.time_snapshot,

                "random_seed":
                    self.deterministic.random_seed,

                "environment_hash":
                    self.deterministic.environment_hash,

                "input_envelope_hash":
                    self.deterministic.input_envelope_hash,

                "deterministic_hash":
                    self.deterministic.deterministic_hash,
            }

        else:

            base[
                "deterministic"
            ] = None

        base[
            "metadata"
        ] = self.metadata

        return base

    # ========================================================
    # IMMUTABLE METADATA
    # ========================================================

    def with_metadata(
        self,
        extra: Dict[str, Any],
    ) -> "RuntimeContext":

        merged = {
            **self.metadata,
            **extra,
        }

        return RuntimeContext(

            authority_profile=
                self.authority_profile,

            payload=
                self.payload,

            replay_requirements=
                self.replay_requirements,

            deterministic=
                self.deterministic,

            metadata=
                merged,

            timestamp=
                self.timestamp,

            context_hash=
                self.context_hash,
        )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "RuntimeContext("
            f"hash="
            f"{self.context_hash[:12]}..."
            ")"
        )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [

    "RuntimeContext",

    "RuntimeContextError",
]