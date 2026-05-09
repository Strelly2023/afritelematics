"""Local deterministic stub inference provider (Phase‑2B).

Purpose:
- Provide a deterministic, offline inference provider
- Serve as the reference implementation for replay‑bound inference
- Enable CI, testing, and evidence harness execution

Guarantees:
- Fully deterministic output
- Canonical inference_binding emission
- No external dependencies
- No authority or governance logic

Authority:
- afritech/docs/execution/CONSTITUTIONAL_RESEARCH_AGENT_SPEC.md
- afritech/replay/REPLAY_VERIFIER_SPEC.md
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

from afritech.inference.providers.base import (
    InferenceProvider,
    ProviderMetadata,
    InferenceOutput,
    InferenceBinding,
    build_inference_binding,
)


# ============================================================
# LOCAL STUB PROVIDER
# ============================================================

class LocalDeterministicStubProvider(InferenceProvider):
    """
    Deterministic local inference provider.

    Characteristics:
    - No external model or network calls
    - Purely functional output based on input hash
    - Deterministic across machines and runs

    This provider is replay‑ideal and should be used for:
    - Phase‑2B evidence harness
    - CI determinism checks
    - Development and testing
    """

    def __init__(
        self,
        *,
        model_id: str = "llm-stub-deterministic-v2",
        model_version: str = "2026-05",
        provider_name: str = "local-deterministic-stub",
    ) -> None:
        """
        Initialize the deterministic stub provider.
        """

        super().__init__(
            ProviderMetadata(
                provider=provider_name,
                model_id=model_id,
                model_version=model_version,
            )
        )


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
        Invoke the deterministic stub model.

        Output is a stable function of the input hash.
        """

        # ----------------------------------------------------
        # Deterministic pseudo-output
        # ----------------------------------------------------

        raw_output: str = self._deterministic_response(prompt, parameters)

        # ----------------------------------------------------

#afritech/inference/providers/local_stub_provider.py

