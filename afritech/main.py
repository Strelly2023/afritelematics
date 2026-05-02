"""
AfriTech Sovereign Entry Point
Constitutional migration bridge: v1 authority enforcement,
new namespace sovereignty declaration.
"""

from importlib import import_module
from pathlib import Path
import sys


def constitutional_halt(message: str):
    raise SystemExit(f"\n❌ CONSTITUTIONAL HALT\n{message}\n")


def load_required(module_path: str):
    try:
        return import_module(module_path)
    except ImportError as e:
        constitutional_halt(
            f"Required authority module missing:\n"
            f"{module_path}\n\n{e}"
        )


print("🏛️ AFRITECH SOVEREIGN BOOT SEQUENCE STARTING")

ROOT = Path(__file__).resolve()

if "afritech_v1" in str(ROOT):
    constitutional_halt(
        "Execution attempted from frozen namespace."
    )

print("🔄 Constitutional migration bridge active")

# ------------------------------------------------------------
# v1 kernel authority (temporary migration bridge)
# ------------------------------------------------------------

print("🔐 Verifying kernel authority...")

v1_main = load_required("afritech_v1.main")

if hasattr(v1_main, "boot"):
    v1_main.boot()
else:
    print("⚠️ Using import-time v1 verification")

print("✅ Kernel authority inherited")

# ------------------------------------------------------------
# Lean formal layer presence
# ------------------------------------------------------------

lean_dir = Path(__file__).parent / "lean"

required_lean = [
    "Kernel.lean",
    "State.lean",
    "Production.lean",
    "Executable.lean",
]

missing = [
    f for f in required_lean
    if not (lean_dir / f).exists()
]

if missing:
    constitutional_halt(
        f"Formal layer incomplete:\n{missing}"
    )

print("✅ Formal constitutional layer present")

# ------------------------------------------------------------
# Sovereign declaration
# ------------------------------------------------------------

print("🏛️ Namespace authority transferred to /afritech")
print("🟢 AfriTech RUNNING (STATE: MIGRATION-SOVEREIGN)")