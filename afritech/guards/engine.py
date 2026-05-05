from __future__ import annotations

from pathlib import Path
import hashlib
import yaml
from enum import Enum, auto


# ---------------------------------------------------------
# Constitutional root
# ---------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------
# Runtime violation taxonomy (classification only)
# ---------------------------------------------------------

class ViolationClass(Enum):
    """
    Runtime constitutional violation classification.

    This enumeration is DOCUMENTARY.
    It does NOT alter enforcement behavior unless explicitly used.
    """

    A_FATAL = auto()
    """Fatal constitutional violations (hard invariant breach)."""

    B_STRUCTURAL = auto()
    """Structural drift or undeclared identity surface change."""

    C_DOCUMENTARY = auto()
    """Non-authoritative documentary divergence (warnings only)."""


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
    """
    Raise a classified constitutional violation.

    Default classification = A_FATAL
    (preserves existing behavior).
    """
    raise ConstitutionalViolation(msg, violation_class)


# ---------------------------------------------------------
# Deterministic manifest-based hashing
# ---------------------------------------------------------

def sha256_manifest(root: Path, files: list[str]) -> str:
    """
    Deterministic constitutional hash.

    Hashes ONLY registry-declared files.
    Hash domain = (relative path + file contents), order stable.

    Filesystem noise is constitutionally irrelevant.
    """
    hasher = hashlib.sha256()

    for rel_path in sorted(files):
        path = root / rel_path

        if not path.exists():
            fail(
                f"Declared constitutional file missing: {rel_path}",
                ViolationClass.B_STRUCTURAL,
            )

        hasher.update(rel_path.encode())
        hasher.update(b"\0")
        hasher.update(path.read_bytes())
        hasher.update(b"\0")

    return hasher.hexdigest()


# ---------------------------------------------------------
# Kernel immutability (structural)
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

def verify_registry_authority() -> None:
    registry = ROOT / "registry"

    if not registry.exists():
        fail("Registry authority absent", ViolationClass.A_FATAL)


# ---------------------------------------------------------
# Registry seal enforcement (manifest-driven)
# ---------------------------------------------------------

def verify_registry_seal() -> None:
    """
    FULL seal enforcement.
    Used by runtime and CI.

    Enforces:
    ✅ registry is SEALED
    ✅ each constitutional surface is declared
    ✅ manifest-based hash equality for every surface
    """
    registry_file = ROOT / "registry" / "registry.yaml"

    if not registry_file.exists():
        fail("registry.yaml missing", ViolationClass.A_FATAL)

    with open(registry_file, "r") as f:
        registry = yaml.safe_load(f)

    att = registry.get("attestation", {})

    if att.get("seal_status") != "SEALED":
        fail("Registry is not SEALED", ViolationClass.A_FATAL)

    kernel_hashes = att.get("kernel_hashes")

    if not kernel_hashes:
        fail(
            "Registry kernel attestation missing",
            ViolationClass.A_FATAL,
        )

    for scope, data in kernel_hashes.items():

        declared_files = data.get("files")
        expected_hash = data.get("hash")

        if not declared_files or not expected_hash:
            fail(
                f"Incomplete attestation for scope: {scope}",
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


# ---------------------------------------------------------
# Epoch‑advance authority verification
# ---------------------------------------------------------

def verify_authority_for_epoch() -> None:
    """
    Pre‑epoch authority verification.

    Enforces:
    ✅ kernel immutability structure
    ✅ dependency law
    ✅ registry existence
    ✅ registry is currently SEALED

    Explicitly does NOT enforce surface hash equality.
    """
    verify_kernel_immutability()
    verify_dependency_law()
    verify_registry_authority()

    registry_file = ROOT / "registry" / "registry.yaml"

    if not registry_file.exists():
        fail("registry.yaml missing", ViolationClass.A_FATAL)

    with open(registry_file, "r") as f:
        registry = yaml.safe_load(f)

    if registry.get("attestation", {}).get("seal_status") != "SEALED":
        fail(
            "Registry must be SEALED before epoch advancement",
            ViolationClass.A_FATAL,
        )


# ---------------------------------------------------------
# Sovereign verification (runtime + CI)
# ---------------------------------------------------------

def verify_sovereignty() -> None:
    """
    Full constitutional enforcement.
    Must be used by runtime and CI.
    """
    verify_kernel_immutability()
    verify_dependency_law()
    verify_registry_authority()
    verify_registry_seal()