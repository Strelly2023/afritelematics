"""
afritech/inference/runtime.py

Phase‑2B inference runtime.

Purpose:
- Invoke a real (or stubbed) model
- Produce a deterministic inference binding
- Preserve replay determinism at the binding boundary

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
- afritech/replay/REPLAY_VERIFIER_SPEC.md
"""

from __future__ import annotations

from typing import Any, Dict, Tuple
import hashlib
import json
import time


# ============================================================
# PUBLIC API
# ============================================================

def invoke_inference(
    *,
    prompt: str,
    parameters: Dict[str, Any],
    provider: str = "local-deterministic-stub",
    model_id: str = "llm-stub-deterministic-v2",
    model_version: str = "2026-05",
) -> Tuple[str, Dict[str, Any]]:
    """
    Invoke a model and return:
      (raw_output, inference_binding)

    IMPORTANT:
    - Raw output is NOT replay-authoritative.
    - Only the inference_binding participates in replay truth.
    - Determinism is enforced at the replay boundary, not by
      probabilistic guarantees of the model itself.
    """

    # --------------------------------------------------------
    # Canonicalize model input (replay-bound)
    # --------------------------------------------------------

    canonical_input = _canonical_json(
        {
            "prompt": prompt,
            "parameters": parameters,
            "provider": provider,
            "model_id": model_id,
            "model_version": model_version,
        }
    )

    input_hash = _sha256(canonical_input)

    # --------------------------------------------------------
    # Dispatch to provider adapter
    # --------------------------------------------------------

    if provider == "local-deterministic-stub":
        raw_output = _invoke_deterministic_stub(
            input_hash=input_hash
        )
    else:
        # Future providers (OpenAI, llama.cpp, hybrid cache)
        # MUST preserve this binding contract.
        raise NotImplementedError(
            f"Inference provider not implemented: {provider}"
        )

    # --------------------------------------------------------
    # Canonicalize output (replay-bound)
    # --------------------------------------------------------

    output_hash = _sha256(_canonical_json(raw_output))

    # --------------------------------------------------------
    # Build inference binding (Phase‑2B artifact)
    # --------------------------------------------------------

    inference_binding: Dict[str, Any] = {
        "provider": provider,
        "model_id": model_id,
        "model_version": model_version,
        "parameters": parameters,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "emitted_at": int(time.time()),
    }

    return raw_output, inference_binding


# ============================================================
# PROVIDER ADAPTERS
# ============================================================

def _invoke_deterministic_stub(
    *,
    input_hash: str,
) -> str:
    """
    Deterministic stub inference.

    NOTE:
    This function is NOT intended to simulate intelligence.
    It exists solely to validate replay‑bound inference mechanics.
    """

    return f"deterministic-output::{input_hash[:16]}"


# ============================================================
# UTILITIES
# ============================================================

def _canonical_json(obj: Any) -> str:
    """
    Canonical JSON serialization for hashing.
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
