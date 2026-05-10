# afritech/proof/build_certificate.py

"""
AfriTech Runtime Certificate Builder
===================================

Assembles a RuntimeCertificate from live constitutional artifacts.

This file is the ONLY authority allowed to construct
a RuntimeCertificate in memory.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from afritech.proof.runtime_certificate import RuntimeCertificate


ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    if not path.exists():
        raise RuntimeError(f"Missing required artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_runtime_certificate() -> RuntimeCertificate:
    """
    Construct a runtime certificate from live constitutional artifacts.
    """

    semantic_ir = ROOT / "afritech/constitution/compiled/invariants_ir.json"
    invariant_index = ROOT / "afritech/constitution/compiled/invariants_index.py"

    lean_invariants = ROOT / "afritech/formal/generated/invariants.lean"
    lean_epochs = ROOT / "afritech/formal/generated/epochs.lean"

    epoch_ir = ROOT / "afritech/epoch/compiled/epoch_ir.json"
    completeness = ROOT / "afritech/proof/completeness.json"

    # NOTE:
    # Execution-level objects (RuntimeContext, ExecutionResult, ProofSnapshot)
    # are intentionally NOT included here yet.
    # This builder is Phase‑5 structural binding only.

    return RuntimeCertificate(
        registry_hash="UNBOUND",

        context=None,               # deferred to execution-time binding
        execution_result=None,
        proof_snapshot=None,

        semantic_compiler_hash=sha256_file(semantic_ir),
        invariant_ir_hash=sha256_file(semantic_ir),
        invariant_index_hash=sha256_file(invariant_index),

        lean_invariant_hash=sha256_file(lean_invariants),
        lean_epoch_hash=sha256_file(lean_epochs),

        epoch_ir_hash=sha256_file(epoch_ir),
        ci_completeness_hash=sha256_file(completeness),

        metadata={"phase": "PHASE_5_STRUCTURAL"},
    )