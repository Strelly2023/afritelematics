"""
afritech/inference/cache/replay_cache.py

Replay-safe inference cache (Phase‑2B).

Purpose:
- Provide a hybrid inference cache keyed by input_hash
- Enable deterministic replay acceptance without re-invoking models
- Enforce deterministic refusal on cache miss during replay

Design principles:
- Cache stores hashes, not semantic truth
- Replay determinism is preserved by construction
- No authority, verifier, or governance logic included

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
- afritech/replay/REPLAY_VERIFIER_SPEC.md
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional
import json
import hashlib


# ============================================================
# REPLAY CACHE
# ============================================================

class ReplayInferenceCache:
    """
    Replay-safe inference cache.

    Cache invariants:
    - Keyed strictly by input_hash
    - Stores output_hash + immutable metadata only
    - NEVER performs inference
    - NEVER mutates stored entries after write

    Replay behavior:
    - Cache hit     → deterministic accept
    - Cache miss    → deterministic refusal (handled by caller)
    """

    def __init__(self, cache_dir: str) -> None:
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)


    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    def lookup(self, *, input_hash: str) -> Optional[Dict[str, Any]]:
        """
        Lookup an inference result by input_hash.

        Returns:
          Cached entry dict if present
          None if cache miss
        """

        path = self._entry_path(input_hash)

        if not path.exists():
            return None

        with path.open("r", encoding="utf-8") as f:
            return json.load(f)


    # --------------------------------------------------------
    # INSERT
    # --------------------------------------------------------

    def store(
        self,
        *,
        input_hash: str,
        output_hash: str,
        provider: str,
        model_id: str,
        model_version: str,
        parameters: Dict[str, Any],
    ) -> None:
        """
        Store an inference binding entry.

        IMPORTANT:
        - This method MUST only be called after a successful
          real inference invocation.
        - Existing entries are immutable and MUST NOT be overwritten.
        """

        path = self._entry_path(input_hash)

        if path.exists():
            # Immutable-by-design: do not overwrite
            return

        entry = {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "provider": provider,
            "model_id": model_id,
            "model_version": model_version,
            "parameters": parameters,
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                entry,
                f,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            )


    # ============================================================
    # INTERNALS
    # ============================================================

    def _entry_path(self, input_hash: str) -> Path:
        """
        Resolve filesystem path for a cache entry.
        """
        self._validate_hash(input_hash)
        return self._cache_dir / f"{input_hash}.json"


    @staticmethod
    def _validate_hash(value: str) -> None:
        """
        Validate that the hash is a canonical SHA‑256 hex string.
        """
        if not isinstance(value, str):
            raise TypeError("Hash must be a string")

        if len(value) != 64:
            raise ValueError("Hash must be 64 hex characters")

        try:
            int(value, 16)
        except ValueError:
            raise ValueError("Hash must be hexadecimal")