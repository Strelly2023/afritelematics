"""
AfriTech Sovereign Entry Point
==============================

Post-migration constitutional authority root.

afritech_v1 is frozen historical lineage only.
No runtime authority may be imported from it.

This file is the exclusive lawful execution gateway for AfriTech.
"""

from __future__ import annotations

from pathlib import Path

from afritech.guards.engine import (
    verify_sovereignty,
    ConstitutionalViolation,
)
from afritech.audit.emitter import emit_event

# ---------------------------------------------------------------------
# Constitutional halt
# ---------------------------------------------------------------------

def constitutional_halt(message: str) -> None:
    raise SystemExit(f"\n❌ CONSTITUTIONAL HALT\n{message}\n")


# ---------------------------------------------------------------------
# Sovereign boot
# ---------------------------------------------------------------------

def boot() -> None:
    print("🏛️ AFRITECH SOVEREIGN BOOT SEQUENCE STARTING")

    root_file = Path(__file__).resolve()

    if "afritech_v1" in str(root_file):
        constitutional_halt(
            "Execution attempted from frozen namespace."
        )

    print("🔐 Verifying constitutional lineage...")

    # ------------------------------------------------------------
    # Historical lineage verification
    # ------------------------------------------------------------

    project_root = root_file.parent.parent
    v1_root = project_root / "afritech_v1"

    required_legacy = [
        "main.py",
        "architecture/kernel_manifest.yaml",
        "registry/registry.yaml",
    ]

    missing_legacy = [
        artifact
        for artifact in required_legacy
        if not (v1_root / artifact).exists()
    ]

    if missing_legacy:
        constitutional_halt(
            "Historical lineage broken:\n"
            f"{missing_legacy}"
        )

    print("✅ Historical lineage preserved")

    # ------------------------------------------------------------
    # Formal + registry + kernel sovereignty verification
    # ------------------------------------------------------------

    try:
        verify_sovereignty()
    except ConstitutionalViolation as e:
        constitutional_halt(str(e))

    print("✅ Formal constitutional layer verified")
    print("✅ Runtime sovereignty verified")
    print("✅ Registry seal verified")

    # ------------------------------------------------------------
    # Runtime execution authority (EXISTENCE first, IMPORT second)
    # ------------------------------------------------------------

    executor_path = project_root / "afritech" / "runtime" / "guard_executor.py"

    if not executor_path.exists():
        constitutional_halt(
            "Runtime execution layer missing:\n"
            "afritech/runtime/guard_executor.py"
        )

    try:
        from afritech.runtime.guard_executor import run
    except Exception as exc:
        constitutional_halt(
            "Runtime execution layer present but failed to load:\n"
            f"{exc}"
        )

    # ------------------------------------------------------------
    # Sovereign declaration
    # ------------------------------------------------------------

    print("🏛️ Authority root: /afritech")
    print("📜 Legacy lineage: preserved (/afritech_v1 frozen)")
    print("🟢 AfriTech RUNNING (STATE: SOVEREIGN)")

    emit_event(
    event_type="RUNTIME_BOOT_SUCCESS",
    severity_class="C_DOCUMENTARY",
    epoch=1,  # or registry-derived current epoch
    adr=None,
    description=(
        "Sovereign runtime boot completed successfully. "
        "All constitutional surfaces verified."
    ),
)

    run()


# ---------------------------------------------------------------------
# Module execution
# ---------------------------------------------------------------------

if __name__ == "__main__":
    boot()