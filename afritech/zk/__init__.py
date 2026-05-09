"""
afritechriTech Zero-Knowledge Moduleafritech/zk/__init__.py
==============================

Public entrypoint for all ZK components.

Exposes:
- ZKProof
- ZKProver
- ZKVerifier
- ZKRegistry

Optional:
- Built-in verifiers (mock, groth16)
- Registry bootstrap helpers
"""

from __future__ import annotations


# -----------------------------------------------------------------
# CORE INTERFACES
# -----------------------------------------------------------------

from .interface import (
    ZKProof,
    ZKProver,
    ZKVerifier,
    ZKError,
)


# -----------------------------------------------------------------
# REGISTRY
# -----------------------------------------------------------------

from .registry import ZKRegistry


# -----------------------------------------------------------------
# OPTIONAL BUILTIN BACKENDS
# -----------------------------------------------------------------

try:
    from .mock_snark import MockSNARKVerifier
except Exception:
    MockSNARKVerifier = None

try:
    from .groth16_verifier import Groth16Verifier
except Exception:
    Groth16Verifier = None

try:
    from .groth16_prover import Groth16Prover
except Exception:
    Groth16Prover = None


# -----------------------------------------------------------------
# REGISTRY BOOTSTRAP
# -----------------------------------------------------------------

def bootstrap_default_zk():
    """
    Register default ZK backends safely.

    Can be called at system startup.
    """

    if MockSNARKVerifier:
        try:
            ZKRegistry.register("mock", MockSNARKVerifier())
        except Exception:
            pass  # ignore duplicate registration

    # NOTE:
    # Groth16Verifier requires verification key path,
    # so it is NOT auto-registered here.


# -----------------------------------------------------------------
# PUBLIC EXPORTS
# -----------------------------------------------------------------

__all__ = [
    "ZKProof",
    "ZKProver",
    "ZKVerifier",
    "ZKRegistry",
    "ZKError",
    "bootstrap_default_zk",
]

