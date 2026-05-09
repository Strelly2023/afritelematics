"""
afritech/inference/providers/llamacpp_provider.py

llama.cpp inference provider (Phase‑2B).

Purpose:
- Provide a concrete InferenceProvider for llama.cpp-based models
- Support fully local / offline inference
- Emit deterministic inference bindings under replay law

IMPORTANT:
- This module does NOT import llama.cpp bindings directly.
- A compatible llama.cpp client MUST be injected.
- Raw model output is NOT replay-authoritative.
- Only the inference_binding participates in replay truth.

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
- afritech/replay/REPLAY_VERIFIER_SPEC.md
"""

from __future__ import annotations

from typing import Any, Dict, Tuple, Protocol

from afritech.inference.providers.base import (
    InferenceProvider,
    ProviderMetadata,
    InferenceOutput,
    InferenceBinding,
    build_inference_binding,
)


# ============================================================
# LLAMA.CPP CLIENT PROTOCOL
# ============================================================

class LlamaCppClientProtocol(Protocol):
    """
    Minimal protocol a llama.cpp-compatible client must satisfy.

    This avoids hard coupling to a specific llama.cpp Python wrapper
    while keeping the execution contract explicit.
    """

    def generate(
        self,
        *,
        prompt: str,
        temperature: float,
        top_p: float,
        max_tokens: int,
        seed: int,
    ) -> str:
        """
        MUST return the generated text as a string.
        """
        ...


# ============================================================
# LLAMA.CPP PROVIDER
# ============================================================

class LlamaCppProvider(InferenceProvider):
    """
    llama.cpp inference provider.

    Guarantees:
    - Local / offline inference
    - Canonical inference_binding emission
    - Replay determinism enforced at binding boundary

    Recommended usage:
    - Phase‑2B evidence harness
    - Deterministic local replay validation
    - High‑control inference environments
    """

    def __init__(
        self,
        *,
        client: LlamaCppClientProtocol,
        model_id: str,
        model_version: str,
        provider_name: str = "llama.cpp",
    ) -> None:
        """
        Initialize the llama.cpp provider.

        Parameters:
          client         : Injected llama.cpp-compatible client
          model_id       : Canonical model identifier (e.g. llama-3-8b)
          model_version  : Model checksum or build identifier
          provider_name  : Stable provider name (default: llama.cpp)
        """

        super().__init__(
            ProviderMetadata(
                provider=provider_name,
                model_id=model_id,
                model_version=model_version,
            )
        )
        self._client = client


    # --------------------------------------------------------
    # INVOCATION
    # --------------------------------------------------------

    def invoke(
        self,
        *,
        prompt: str,
        parameters: Dict[str, Any],
    ) -> Tuple[InferenceOutput, InferenceBinding]:
        """
        Invoke the llama.cpp model.

        Required parameters (validated by caller or CI):
          - temperature
          - top_p
          - max_tokens
          - seed

        The seed parameter enables deterministic generation,
        but replay determinism is enforced via binding hashes
        regardless of generation behavior.
        """

        # ----------------------------------------------------
        # Extract parameters with safe defaults
        # ----------------------------------------------------

        temperature: float = float(parameters.get("temperature", 0.0))
        top_p: float = float(parameters.get("top_p", 1.0))
        max_tokens: int = int(parameters.get("max_tokens", 256))
        seed: int = int(parameters.get("seed", 42))

        # ----------------------------------------------------
        # Invoke llama.cpp client (may be deterministic or not)
        # ----------------------------------------------------

        raw_output: str = self._client.generate(
            prompt=prompt,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            seed=seed,
        )

        # ----------------------------------------------------
        # Build deterministic inference binding
        # ----------------------------------------------------

        inference_binding: InferenceBinding = build_inference_binding(
            metadata=self.metadata,
            parameters=parameters,
            prompt=prompt,
            raw_output=raw_output,
        )

        return raw_output, inference_binding