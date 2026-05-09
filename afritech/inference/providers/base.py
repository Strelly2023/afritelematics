"""/base.py

Canonical inference provider base definitions.

Purpose:
- Define the strict interface for inference providers
- Enforce Phase‑2B inference binding contract
- Prevent provider-specific logic from contaminating replay law

All inference providers MUST implement this interface.

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
- afritech/replay/REPLAY_VERIFIER_SPEC.md
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Tuple
import hashlib
import json
import time


# ============================================================
# INFERENCE RESULT TYPES
# ============================================================

InferenceOutput = str
InferenceBinding = Dict[str, Any]


# ============================================================
# PROVIDER METADATA
# ============================================================

@dataclass(frozen=True)
class ProviderMetadata:
    """
    Immutable description of an inference provider.

    This metadata is replay-bound and MUST be stable.
    """
    provider: str
    model_id: str
    model_version: str


# ============================================================
# BASE PROVIDER INTERFACE
# ============================================================

class InferenceProvider(ABC):
    """
    Abstract base class for all inference providers.

    Contract:
    - Providers MAY be nondeterministic internally
    - Providers MUST emit deterministic inference bindings
    - Providers MUST NOT enforce authority or governance
    """

    metadata: ProviderMetadata

    # --------------------------------------------------------
    # PROVIDER IDENTITY
    # --------------------------------------------------------

    def __init__(self, metadata: ProviderMetadata) -> None:
        self.metadata = metadata

    # --------------------------------------------------------
    # INVOCATION ENTRYPOINT
    # --------------------------------------------------------

    @abstractmethod
    def invoke(
        self,
        *,
        prompt: str,
        parameters: Dict[str, Any],
    ) -> Tuple[InferenceOutput, InferenceBinding]:
        """
        Invoke the underlying model.

        MUST return:
          (raw_output, inference_binding)

        Rules:
        - raw_output may be probabilistic
        - inference_binding MUST be deterministic
        - inference_binding MUST include:
            provider
            model_id
            model_version
            parameters
            input_hash
            output_hash
            emitted_at
        """
        raise NotImplementedError


# ============================================================
# SHARED BINDING UTILITIES
# ============================================================

def build_inference_binding(
    *,
    metadata: ProviderMetadata,
    parameters: Dict[str, Any],
    prompt: str,
    raw_output: str,
) -> InferenceBinding:
    """
    Build a canonical inference binding.

    This helper enforces the Phase‑2B binding contract
    and should be used by all providers unless a
    stricter binding is required.
    """

    canonical_input = _canonical_json(
        {
            "prompt": prompt,
            "parameters": parameters,
            "provider": metadata.provider,
            "model_id": metadata.model_id,
            "model_version": metadata.model_version,
        }
    )

    input_hash = _sha256(canonical_input)
    output_hash = _sha256(_canonical_json(raw_output))

    return {
        "provider": metadata.provider,
        "model_id": metadata.model_id,
        "model_version": metadata.model_version,
        "parameters": parameters,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "emitted_at": int(time.time()),
    }


# ============================================================
# CANONICAL HASHING UTILITIES
# ============================================================

def _canonical_json(obj: Any) -> str:
    """
    Canonical JSON serialization for replay hashing.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(value: str) -> str:
    """
    SHA‑256 hex digest helper.
    """
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

