"""
Shared Runtime Context
======================

Neutral, dependency-free representation of execution context.

Constitutional guarantees:

- deterministic replay-safe serialization
- immutable runtime metadata
- dependency isolation
- stable context hashing
- closed-world execution compatibility

This module MUST NOT import:

- runtime.engine
- runtime.guards
- replay.verifier
"""

from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass, field
from typing import Any, Dict


# ============================================================
# CONTEXT
# ============================================================

@dataclass(frozen=True)
class RuntimeContext:
    """
    Shared runtime context used across:

    - runtime execution
    - replay verification
    - constitutional enforcement
    - property testing
    - witness generation
    """

    # --------------------------------------------------------
    # constitutional authority
    # --------------------------------------------------------

    authority_profile: str

    # --------------------------------------------------------
    # deterministic execution payload
    # --------------------------------------------------------

    payload: Dict[str, Any]

    # --------------------------------------------------------
    # replay semantics
    # --------------------------------------------------------

    replay_requirements: Dict[str, Any]

    # --------------------------------------------------------
    # deterministic timestamp
    # --------------------------------------------------------

    timestamp: str | None = None

    # --------------------------------------------------------
    # replay-safe deterministic context hash
    # --------------------------------------------------------

    context_hash: str = field(
        default="",
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __post_init__(
        self,
    ) -> None:

        # ----------------------------------------------------
        # auto-generate deterministic hash if absent
        # ----------------------------------------------------

        if not self.context_hash:

            generated = (
                self._generate_hash()
            )

            object.__setattr__(
                self,
                "context_hash",
                generated,
            )

    # ========================================================
    # DETERMINISTIC HASHING
    # ========================================================

    def _generate_hash(
        self,
    ) -> str:

        canonical = {

            "authority_profile":
                self.authority_profile,

            "payload":
                self.payload,

            "replay_requirements":
                self.replay_requirements,

            "timestamp":
                self.timestamp,
        }

        encoded = json.dumps(

            canonical,

            sort_keys=True,

            separators=(
                ",",
                ":",
            ),

            ensure_ascii=False,

        ).encode(
            "utf-8"
        )

        return hashlib.sha256(
            encoded
        ).hexdigest()

    # ========================================================
    # INTEGRITY
    # ========================================================

    def verify(
        self,
    ) -> bool:
        """
        Deterministic replay-safe integrity validation.
        """

        try:

            expected = (
                self._generate_hash()
            )

        except Exception:

            return False

        return (
            expected
            == self.context_hash
        )

    # ========================================================
    # SERIALIZATION
    # ========================================================

    def to_dict(
        self,
    ) -> Dict[str, Any]:

        return {

            "authority_profile":
                self.authority_profile,

            "payload":
                self.payload,

            "replay_requirements":
                self.replay_requirements,

            "context_hash":
                self.context_hash,

            "timestamp":
                self.timestamp,
        }

    # ========================================================
    # REPR
    # ========================================================

    def __repr__(
        self,
    ) -> str:

        return (

            "RuntimeContext("
            f"authority_profile="
            f"{self.authority_profile!r}, "
            f"context_hash="
            f"{self.context_hash[:12]}..."
            ")"
        )