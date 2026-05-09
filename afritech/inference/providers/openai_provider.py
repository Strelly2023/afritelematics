"""
 default.afritech/inference/providers/openai_provider.py
- A compliant OpenAI client MUST be injected explicitly.
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
# OPENAI CLIENT PROTOCOL
# ============================================================

class OpenAIClientProtocol(Protocol):
    """
    Minimal protocol an OpenAI-compatible client must satisfy.

    This avoids a hard dependency on any specific OpenAI SDK
    version while keeping the contract explicit.
    """

    def create_chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        top_p: float,
        max_tokens: int,
    ) -> str:
        """
        MUST return the assistant message content as a string.
        """
        ...


# ============================================================
# OPENAI PROVIDER
# ============================================================

class OpenAIProvider(InferenceProvider):
    """
    OpenAI inference provider.

    Guarantees:
    - Emits canonical inference_binding objects
    - Does NOT enforce authority or replay policy
    - Supports deterministic replay via binding hashes

    Non‑goals:
    - Semantic correctness
    - Output determinism at generation time
    """

    def __init__(
        self,
        *,
        client: OpenAIClientProtocol,
        model_id: str,
        model_version: str,
        provider_name: str = "openai",
    ) -> None:
        """
        Initialize the OpenAI provider.

        Parameters:
          client        : Injected OpenAI-compatible client
          model_id      : Canonical model identifier (e.g. gpt-4o)
          model_version : Provider-declared model version
          provider_name : Stable provider identifier (default: openai)
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
        Invoke the OpenAI model.

        Required parameters (validated by caller or CI):
          - temperature
          - top_p
          - max_tokens

        This method:
        - Calls the injected OpenAI client
        - Receives raw output
        - Constructs a deterministic inference_binding
        """

        # ----------------------------------------------------
        # Invoke OpenAI client (non-deterministic allowed)
        # ----------------------------------------------------

        raw_output: str = self._client.create_chat_completion(
            model=self.metadata.model_id,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=float(parameters.get("temperature", 0.0)),
            top_p=float(parameters.get("top_p", 1.0)),
            max_tokens=int(parameters.get("max_tokens", 256)),
        )

        # ----------------------------------------------------
        # Build deterministic inference binding
        # ----------------------------------------------------

        inference_binding = build_inference_binding(
            metadata=self.metadata,
            parameters=parameters,
            prompt=prompt,
            raw_output=raw_output,
        )

        return raw_output, inference_binding
''' 

OpenAI inference provider (Phase‑2B).

Purpose:
- Provide a concrete InferenceProvider implementation for OpenAI models
- Emit deterministic inference bindings under replay law
- Keep OpenAI client usage fully isolated from governance and replay logic

IMPORTANT:
'''