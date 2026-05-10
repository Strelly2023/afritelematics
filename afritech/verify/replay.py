# afritech/verify/replay.py

"""
AfriTech Constitutional Replay Verifier
======================================

CLI entrypoint for machine-checkable constitutional replay verification.

Replay verification is AUTHORITATIVE in afritech.verify.engine.verify_replay.
This file is an observer and reporter only.

Replay is law.
If replay fails, legitimacy does not exist.
"""

from __future__ import annotations

import sys
from typing import Optional

from afritech.verify.engine import verify_replay
from afritech.verify.report import print_report

from afritech.registry.loader import load_registry
from afritech.guards.engine import fail, ViolationClass


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    """
    Execute constitutional replay verification.

    Exit codes:
      0 -> Replay VALID (constitutional history lawful)
      1 -> Replay INVALID (constitutional legitimacy void)
    """

    print("🔁 AFRITECH CONSTITUTIONAL REPLAY VERIFIER")
    print("--------------------------------------------------")

    # -------------------------------------------------------------
    # LOAD REGISTRY (SINGULAR AUTHORITY)
    # -------------------------------------------------------------

    print("• Loading sealed registry...")
    registry = load_registry()

    attestation = registry.get("attestation")
    if not attestation:
        fail(
            "missing_registry_attestation",
            ViolationClass.A_FATAL,
        )

    if attestation.get("seal_status") != "SEALED":
        fail(
            "registry_not_sealed",
            ViolationClass.A_FATAL,
        )

    print("• Registry is sealed")

    # -------------------------------------------------------------
    # AUTHORITATIVE REPLAY VERIFICATION
    # -------------------------------------------------------------

    print("• Verifying constitutional history via replay engine...")
    print("--------------------------------------------------")

    # IMPORTANT:
    # verify_replay() is the SOLE authority on replay validity.
    result = verify_replay()

    # Normalize error list
    if not hasattr(result, "errors"):
        result.errors = []

    # -------------------------------------------------------------
    # REPORT (NON-AUTHORITATIVE)
    # -------------------------------------------------------------

    print_report(result)

    # -------------------------------------------------------------
    # FINAL VERDICT
    # -------------------------------------------------------------

    if result.valid:
        print("✅ REPLAY VALID")
        print("✅ Constitutional history is lawful")
        sys.exit(0)

    else:
        print("❌ REPLAY INVALID")
        print("❌ Constitutional legitimacy is void")

        if result.errors:
            print("❌ REPLAY VIOLATIONS DETECTED")
            for i, err in enumerate(result.errors, start=1):
                print(f"  {i}. {err}")

        sys.exit(1)


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()