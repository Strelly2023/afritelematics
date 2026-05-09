# afritech/verify/replay.py

from __future__ import annotations

"""
AfriTech Constitutional Replay Verifier
=======================================

CLI entrypoint for machine-checkable constitutional replay verification.

This verifier proves that the current AfriTech sovereign state is the
lawful result of its entire constitutional history.

IMPORTANT CONSTITUTIONAL GUARANTEES:
- Read-only
- Non-authoritative
- No runtime or guard coupling
- No mutation of registry, epochs, or audit logs
- Failure indicates UNLAWFUL HISTORY, not enforcement
"""

import sys
from typing import Optional

from afritech.verify.engine import verify_replay
from afritech.verify.report import print_report

from afritech.trace.trace_reconstructor import reconstruct_trace
from afritech.trace.trace_validator import validate_trace
from afritech.registry.loader import load_registry


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    """
    Execute constitutional replay verification.

    Exit codes:
      0 -> Replay valid
      1 -> Replay invalid
    """

    print("🔁 AFRITECH CONSTITUTIONAL REPLAY")
    print("Loading epoch history...")
    print("Verifying epoch chain...")
    print("Verifying reseal continuity...")
    print("Verifying registry attestation...")
    print("Verifying invariant preservation...")
    print("Verifying ADR legitimacy...")
    print("Reconstructing execution trace...")
    print("Verifying causal trace integrity...")

    # -------------------------------------------------------------
    # CORE REPLAY VERIFICATION (AUTHORITATIVE)
    # -------------------------------------------------------------

    result = verify_replay()

    # -------------------------------------------------------------
    # NORMALIZE RESULT OBJECT (DEFENSIVE)
    # -------------------------------------------------------------

    if not hasattr(result, "errors"):
        result.errors = []

    trace_error: Optional[str] = None

    # -------------------------------------------------------------
    # TRACE VERIFICATION (OPTIONAL, NON-AUTHORITATIVE)
    # -------------------------------------------------------------

    try:
        if result.valid and hasattr(result, "epoch_history") and result.epoch_history:

            registry = load_registry()

            trace = reconstruct_trace(
                epoch_history=result.epoch_history,
                registry=registry,
            )

            validate_trace(trace)

            # -----------------------------------------------------
            # TRACE ↔ REGISTRY BINDING (OPTIONAL)
            # -----------------------------------------------------

            attestation = registry.get("attestation", {})
            expected_trace_hash = attestation.get("trace_hash")

            if expected_trace_hash:
                actual_trace_hash = trace.get("trace_root_hash")

                if actual_trace_hash != expected_trace_hash:
                    raise RuntimeError(
                        "trace_hash_mismatch: "
                        f"{actual_trace_hash} != {expected_trace_hash}"
                    )

    except Exception as e:
        trace_error = str(e)
        result.valid = False
        result.errors.append(
            f"TRACE VERIFICATION FAILED: {trace_error}"
        )

    # -------------------------------------------------------------
    # REPORT
    # -------------------------------------------------------------

    print_report(result)

    # -------------------------------------------------------------
    # EXIT CODE
    # -------------------------------------------------------------

    if result.valid:
       # print("✅ Replay valid")
        #print("✅ Constitutional lineage intact")

        if trace_error is None:
            print("✅ Trace integrity verified")

        sys.exit(0)

    else:
        print("❌ Replay invalid")

        if trace_error:
            print(f"❌ Trace error: {trace_error}")

        sys.exit(1)


# ---------------------------------------------------------------------
# CLI ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()