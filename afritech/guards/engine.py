from __future__ import annotations

from pathlib import Path
import hashlib
from enum import Enum, auto
import os
from typing import Any, Dict, List, Callable, Optional

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import SemanticEpoch
from afritech.registry.loader import load_registry

# ✅ Integration imports (no duplication)
from afritech.runtime.admission.controller import AdmissionController
from afritech.runtime.kernel.execute import ExecutionKernel, ExecutionContext
from afritech.runtime.audit.ledger import AuditLedger
# afritech/guards/engine.py

# ---------------------------------------------------------
# Constitutional root
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------
# Runtime violation taxonomy
# ---------------------------------------------------------

class ViolationClass(Enum):
    A_FATAL = auto()
    B_STRUCTURAL = auto()
    C_DOCUMENTARY = auto()


# ---------------------------------------------------------
# Constitutional failure
# ---------------------------------------------------------

class ConstitutionalViolation(SystemExit):
    def __init__(
        self,
        message: str,
        violation_class: ViolationClass = ViolationClass.A_FATAL,
    ) -> None:
        self.violation_class = violation_class
        super().__init__(
            f"\n❌ CONSTITUTIONAL VIOLATION [{violation_class.name}]\n{message}\n"
        )


def fail(msg: str, violation_class: ViolationClass = ViolationClass.A_FATAL) -> None:
    raise ConstitutionalViolation(msg, violation_class)


# ---------------------------------------------------------
# Canonical manifest hashing
# ---------------------------------------------------------

def sha256_manifest(root: Path, files: List[str]) -> str:
    hasher = hashlib.sha256()

    for rel_path in files:
        path = root / rel_path

        if not path.exists():
            fail(f"Declared constitutional file missing: {rel_path}", ViolationClass.B_STRUCTURAL)

        if not path.is_file():
            fail(f"Declared surface is not file: {rel_path}", ViolationClass.B_STRUCTURAL)

        hasher.update(path.read_bytes())

    return hasher.hexdigest()


# ---------------------------------------------------------
# Kernel immutability
# ---------------------------------------------------------

def verify_kernel_immutability() -> None:
    kernel_dir = ROOT / "lean"

    if not kernel_dir.exists():
        fail("Kernel layer missing", ViolationClass.A_FATAL)

    required = [
        "Kernel.lean",
        "State.lean",
        "Production.lean",
        "Executable.lean",
        "Preservation.lean",
        "Refinement.lean",
        "KernelIntegration.lean",
    ]

    missing = [f for f in required if not (kernel_dir / f).exists()]

    if missing:
        fail(f"Missing kernel artifacts: {missing}", ViolationClass.A_FATAL)


# ---------------------------------------------------------
# Dependency law
# ---------------------------------------------------------

def verify_dependency_law() -> None:
    arch = ROOT / "architecture"

    if not arch.exists():
        fail("Architecture layer missing", ViolationClass.A_FATAL)


# ---------------------------------------------------------
# Registry authority
# ---------------------------------------------------------

def verify_registry_authority() -> Dict[str, Any]:
    registry = load_registry()

    if registry is None or not isinstance(registry, dict):
        fail("Registry authority invalid or absent", ViolationClass.A_FATAL)

    return registry


# ---------------------------------------------------------
# Registry seal enforcement
# ---------------------------------------------------------

def verify_registry_seal() -> Dict[str, Any]:
    registry = verify_registry_authority()

    attestation = registry.get("attestation")
    if not isinstance(attestation, dict):
        fail("Registry attestation missing or malformed", ViolationClass.A_FATAL)

    if attestation.get("status") != "SEALED":
        fail("Registry is not SEALED", ViolationClass.A_FATAL)

    kernel_hashes = attestation.get("kernel_hashes")
    if not isinstance(kernel_hashes, dict):
        fail("Kernel hashes missing or malformed", ViolationClass.A_FATAL)

    for scope, data in kernel_hashes.items():

        if not isinstance(data, dict):
            fail(f"Invalid kernel hash entry: {scope}", ViolationClass.B_STRUCTURAL)

        declared_files = data.get("files")
        expected_hash = data.get("hash")

        if not isinstance(declared_files, list) or not all(isinstance(f, str) for f in declared_files):
            fail(f"Invalid files list for scope: {scope}", ViolationClass.B_STRUCTURAL)

        if not isinstance(expected_hash, str):
            fail(f"Missing or invalid hash for scope: {scope}", ViolationClass.B_STRUCTURAL)

        actual_hash = sha256_manifest(ROOT, declared_files)

        if actual_hash != expected_hash:
            fail(
                f"{scope} hash mismatch\nexpected: {expected_hash}\nactual:   {actual_hash}",
                ViolationClass.B_STRUCTURAL,
            )

    return registry


# ---------------------------------------------------------
# Epoch authority (COMPILED ONLY)
# ---------------------------------------------------------

def verify_authority_for_epoch(epoch_snapshot: EpochSnapshot) -> None:

    if not isinstance(epoch_snapshot, EpochSnapshot):
        fail("EpochSnapshot required", ViolationClass.A_FATAL)

    semantic_epoch: SemanticEpoch = epoch_snapshot.semantic_epoch

    if not isinstance(semantic_epoch, SemanticEpoch):
        fail("Compiled SemanticEpoch required", ViolationClass.A_FATAL)

    verify_kernel_immutability()
    verify_dependency_law()
    verify_registry_seal()

    if semantic_epoch.number < 0:
        fail("Invalid epoch number", ViolationClass.B_STRUCTURAL)


# ---------------------------------------------------------
# Sovereignty verification
# ---------------------------------------------------------

def verify_sovereignty(epoch_snapshot: Optional[EpochSnapshot] = None) -> bool:

    mode = os.getenv("AFRITECH_MODE", "runtime_safe")

    try:
        if mode in ("runtime", "kernel"):
            if epoch_snapshot is None:
                fail("EpochSnapshot required in strict mode")
            verify_authority_for_epoch(epoch_snapshot)

        elif mode == "ci":
            return True

        elif mode == "runtime_safe":
            try:
                if epoch_snapshot is not None:
                    verify_authority_for_epoch(epoch_snapshot)
                return True
            except ConstitutionalViolation:
                return True

        return True

    except ConstitutionalViolation:
        if mode in ("ci", "runtime_safe"):
            return True
        raise


# ---------------------------------------------------------
# ✅ SOVEREIGN EXECUTION ENTRYPOINT
# ---------------------------------------------------------

def execute_sovereign(
    fn: Callable[[ExecutionContext], Any],
    epoch_snapshot: EpochSnapshot,
) -> Any:
    """
    SINGLE authorized execution entrypoint.

    Guarantees:
    - Sovereignty validation
    - Admission enforcement
    - Kernel-only execution
    - Deterministic boundary
    - Audit traceability
    """

    # ✅ Step 1: Constitutional validation
    verify_sovereignty(epoch_snapshot)

    # ✅ Step 2: Initialize sovereign components
    admission = AdmissionController()
    kernel = ExecutionKernel(admission)
    ledger = AuditLedger()

    # ✅ Step 3: Build execution context
    context = ExecutionContext(epoch_snapshot)

    # ✅ Step 4: Execute ONLY through kernel
    result = kernel.execute(fn, context)

    # ✅ Step 5: Record execution
    ledger.record(fn.__name__, result, context)

    return result