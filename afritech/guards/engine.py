from __future__ import annotations

from pathlib import Path
import hashlib
from enum import Enum, auto

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import SemanticEpoch
from afritech.registry.loader import load_registry


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


def fail(
    msg: str,
    violation_class: ViolationClass = ViolationClass.A_FATAL,
) -> None:
    raise ConstitutionalViolation(msg, violation_class)


# ---------------------------------------------------------
# Canonical manifest hashing
# (MUST MATCH registry/seal.py EXACTLY)
# ---------------------------------------------------------

def sha256_manifest(root: Path, files: list[str]) -> str:
    """
    Deterministic constitutional hashing.

    Rules:
    - registry-declared order is authoritative
    - file bytes only
    - no path hashing
    - no sorting
    - no normalization
    """

    hasher = hashlib.sha256()

    for rel_path in files:
        path = root / rel_path

        if not path.exists():
            fail(
                f"Declared constitutional file missing: {rel_path}",
                ViolationClass.B_STRUCTURAL,
            )

        if not path.is_file():
            fail(
                f"Declared surface is not file: {rel_path}",
                ViolationClass.B_STRUCTURAL,
            )

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

    missing = [
        f for f in required
        if not (kernel_dir / f).exists()
    ]

    if missing:
        fail(
            f"Missing kernel artifacts: {missing}",
            ViolationClass.A_FATAL,
        )


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

def verify_registry_authority() -> dict:
    """
    Load and return the sealed registry.

    Guards are allowed to READ the registry,
    but never to mutate or reinterpret it.
    """
    registry = load_registry()

    if not registry:
        fail("Registry authority absent", ViolationClass.A_FATAL)

    return registry


# ---------------------------------------------------------
# Registry seal enforcement
# ---------------------------------------------------------

def verify_registry_seal() -> dict:
    registry = verify_registry_authority()

    attestation = registry.get("attestation")
    if not attestation:
        fail("Registry attestation missing", ViolationClass.A_FATAL)

    if attestation.get("status") != "SEALED":
        fail("Registry is not SEALED", ViolationClass.A_FATAL)

    kernel_hashes = attestation.get("kernel_hashes")
    if not kernel_hashes:
        fail(
            "Registry kernel attestation missing",
            ViolationClass.A_FATAL,
        )

    # Verify kernel hashes deterministically
    for scope, data in kernel_hashes.items():
        declared_files = data.get("files")
        expected_hash = data.get("hash")

        if not declared_files:
            fail(
                f"No files declared for scope: {scope}",
                ViolationClass.B_STRUCTURAL,
            )

        if not expected_hash:
            fail(
                f"Missing hash for scope: {scope}",
                ViolationClass.B_STRUCTURAL,
            )

        actual_hash = sha256_manifest(ROOT, declared_files)

        if actual_hash != expected_hash:
            fail(
                f"{scope} hash mismatch\n"
                f"expected: {expected_hash}\n"
                f"actual:   {actual_hash}",
                ViolationClass.B_STRUCTURAL,
            )

    return registry


# ---------------------------------------------------------
# Epoch authority (COMPILED ONLY)
# ---------------------------------------------------------

def verify_authority_for_epoch(
    epoch_snapshot: EpochSnapshot,
) -> None:
    """
    Guards MUST receive an EpochSnapshot.
    They must never load or parse epoch YAML.
    """

    if not isinstance(epoch_snapshot, EpochSnapshot):
        fail(
            "EpochSnapshot required for epoch authority verification",
            ViolationClass.A_FATAL,
        )

    semantic_epoch: SemanticEpoch = epoch_snapshot.semantic_epoch

    if not isinstance(semantic_epoch, SemanticEpoch):
        fail(
            "Compiled SemanticEpoch required",
            ViolationClass.A_FATAL,
        )

    verify_kernel_immutability()
    verify_dependency_law()
    verify_registry_seal()

    # Epoch structural sanity only
    if semantic_epoch.number < 0:
        fail(
            "Invalid epoch number",
            ViolationClass.B_STRUCTURAL,
        )


# ---------------------------------------------------------
# Sovereignty verification
# ---------------------------------------------------------




def verify_sovereignty(epoch_snapshot: EpochSnapshot) -> None:
    """
    Top-level guard for constitutional sovereignty.

    Requires:
    - sealed registry
    - immutable kernel
    - compiled epoch semantics
    """

    verify_authority_for_epoch(epoch_snapshot)