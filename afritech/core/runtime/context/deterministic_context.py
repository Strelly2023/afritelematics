
#afritech/core/runtime/context/deterministic_context.py
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


@dataclass(frozen=True)
class DeterministicContext:
    """
    Deterministic execution contract.

    This object defines ALL non-code inputs that could otherwise
    introduce nondeterminism.

    If execution differs while this context is identical,
    the system is constitutionally invalid.
    """

    time_snapshot: str
    random_seed: str
    environment_hash: str
    input_envelope_hash: str

    # ---------------------------------------------------------
    # CANONICAL HASH (REPLAY ANCHOR)
    # ---------------------------------------------------------

    @property
    def deterministic_hash(self) -> str:
        """
        Canonical deterministic context hash.

        This hash MUST be stable across:
        - replay
        - distributed verification
        - federation verification
        """

        payload = {
            "time_snapshot": self.time_snapshot,
            "random_seed": self.random_seed,
            "environment_hash": self.environment_hash,
            "input_envelope_hash": self.input_envelope_hash,
        }

        return hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()