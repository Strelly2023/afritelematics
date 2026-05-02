"""
AfriTech Sovereign Entry Point

Post-migration constitutional authority root.

afritech_v1 is frozen historical lineage only.
No runtime authority may be imported from it.
"""

from pathlib import Path


def constitutional_halt(message: str):
    raise SystemExit(f"\n❌ CONSTITUTIONAL HALT\n{message}\n")


print("🏛️ AFRITECH SOVEREIGN BOOT SEQUENCE STARTING")

ROOT = Path(__file__).resolve()

if "afritech_v1" in str(ROOT):
    constitutional_halt(
        "Execution attempted from frozen namespace."
    )

print("🔐 Verifying constitutional lineage...")

# ------------------------------------------------------------
# Historical lineage check
# ------------------------------------------------------------

v1_root = ROOT.parent.parent / "afritech_v1"

required_legacy = [
    "main.py",
    "architecture/kernel_manifest.yaml",
    "registry/registry.yaml",
]

missing_legacy = [
    f for f in required_legacy
    if not (v1_root / f).exists()
]

if missing_legacy:
    constitutional_halt(
        f"Historical lineage broken:\n{missing_legacy}"
    )

print("✅ Historical lineage preserved")

# ------------------------------------------------------------
# Lean constitutional layer
# ------------------------------------------------------------

lean_dir = ROOT.parent / "lean"

required_lean = [
    "Kernel.lean",
    "State.lean",
    "Production.lean",
    "Executable.lean",
    "Preservation.lean",
    "Refinement.lean",
    "KernelIntegration.lean",
]

missing_lean = [
    f for f in required_lean
    if not (lean_dir / f).exists()
]

if missing_lean:
    constitutional_halt(
        f"Formal constitutional layer incomplete:\n{missing_lean}"
    )

print("✅ Formal constitutional layer verified")

# ------------------------------------------------------------
# Runtime sovereignty
# ------------------------------------------------------------

runtime_executor = ROOT.parent / "runtime" / "guard_executor.py"

if not runtime_executor.exists():
    constitutional_halt(
        "Runtime execution layer missing:\n"
        "afritech/runtime/guard_executor.py"
    )

print("✅ Runtime sovereignty verified")

# ------------------------------------------------------------
# Sovereign declaration
# ------------------------------------------------------------

print("🏛️ Authority root: /afritech")
print("📜 Legacy lineage: preserved (/afritech_v1 frozen)")
print("🟢 AfriTech RUNNING (STATE: SOVEREIGN)")