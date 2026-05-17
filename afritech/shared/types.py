"""
Shared Runtime Types
====================

Pure shared runtime data structures.

This module MUST NOT depend on:

- runtime.engine
- execution orchestrators
- guards
- replay verifier internals

Constitutional guarantees:

- deterministic serialization
- replay-safe hashing
- immutable execution artifacts
- canonical witness binding
- side-effect free logic
"""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


# ============================================================
# HELPERS
# ============================================================

def canonical_json(
    data: Any,
) -> str:
    """
    Deterministic replay-safe JSON serialization.
    """

    return json.dumps(

        data,

        sort_keys=True,

        separators=(
            ",",
            ":",
        ),

        ensure_ascii=False,

    )


def stable_hash(
    data: Any,
) -> str:
    """
    Stable replay-safe SHA256 hash.
    """

    encoded = canonical_json(
        data
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        encoded
    ).hexdigest()


# ============================================================
# EXECUTION RESULT
# ============================================================

@dataclass(frozen=True)
class ExecutionResult:
    """
    Deterministic runtime execution result.

    Guarantees:

    - immutable result topology
    - replay-safe serialization
    - canonical witness hashing
    - deterministic proof binding
    """

    # --------------------------------------------------------
    # execution status
    # --------------------------------------------------------

    success: bool

    # --------------------------------------------------------
    # deterministic output
    # --------------------------------------------------------

    output: Dict[str, Any] = field(
        default_factory=dict
    )

    # --------------------------------------------------------
    # replay-safe error surface
    # --------------------------------------------------------

    error: Optional[str] = None

    # --------------------------------------------------------
    # execution context
    # --------------------------------------------------------

    context: Any = None

    # --------------------------------------------------------
    # constitutional proof objects
    # --------------------------------------------------------

    proof: Any = None

    zk_proof: Any = None

    # --------------------------------------------------------
    # deterministic trace binding
    # --------------------------------------------------------

    trace_hash: Optional[str] = None

    # --------------------------------------------------------
    # deterministic timestamp
    # --------------------------------------------------------

    timestamp: str = "UNDEFINED_TIMESTAMP"

    # --------------------------------------------------------
    # replay-safe result hash
    # --------------------------------------------------------

    result_hash: str = field(
        default="",
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        # ----------------------------------------------------
        # derive timestamp from context
        # ----------------------------------------------------

        if (
            self.context
            and hasattr(
                self.context,
                "timestamp",
            )
        ):

            object.__setattr__(
                self,
                "timestamp",
                self.context.timestamp
                or "UNDEFINED_TIMESTAMP",
            )

        # ----------------------------------------------------
        # generate deterministic result hash
        # ----------------------------------------------------

        if not self.result_hash:

            generated = (
                self._compute_hash()
            )

            object.__setattr__(
                self,
                "result_hash",
                generated,
            )

    # ========================================================
    # HASHING
    # ========================================================

    def _hash_payload(
        self,
    ) -> Dict[str, Any]:

        return {

            "success":
                self.success,

            "output":
                self.output,

            "error":
                self.error,

            "trace_hash":
                self.trace_hash,

            "timestamp":
                self.timestamp,
        }

    def _compute_hash(
        self,
    ) -> str:

        return stable_hash(
            self._hash_payload()
        )

    # ========================================================
    # VERIFICATION
    # ========================================================

    def verify(
        self,
    ) -> bool:
        """
        Replay-safe integrity validation.
        """

        try:

            expected = (
                self._compute_hash()
            )

        except Exception:

            return False

        return (
            expected
            == self.result_hash
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {

            "success":
                self.success,

            "output":
                self.output,

            "error":
                self.error,

            "context":
                (
                    self.context.to_dict()
                    if (
                        self.context
                        and hasattr(
                            self.context,
                            "to_dict",
                        )
                    )
                    else None
                ),

            "result_hash":
                self.result_hash,

            "trace_hash":
                self.trace_hash,

            "timestamp":
                self.timestamp,

            "proof":
                (
                    self.proof.to_dict()
                    if (
                        self.proof
                        and hasattr(
                            self.proof,
                            "to_dict",
                        )
                    )
                    else self.proof
                ),

            "zk_proof":
                (
                    self.zk_proof.to_dict()
                    if (
                        self.zk_proof
                        and hasattr(
                            self.zk_proof,
                            "to_dict",
                        )
                    )
                    else self.zk_proof
                ),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "ExecutionResult("
            f"success={self.success}, "
            f"hash={self.result_hash[:12]}..."
            ")"
        )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [

    "canonical_json",

    "stable_hash",

    "ExecutionResult",
]