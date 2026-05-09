# afritech/runtime/main.py

"""
AfriTech Runtime Entry Point

This module defines the constitutional entry point for the AfriTech runtime.

IMPORTANT CONSTITUTIONAL NOTES:
- This file anchors runtime identity and admission ONLY
- It does NOT contain execution logic
- It must NEVER bypass guards or registry enforcement
- All execution must be mediated by constitutional guards
- Runtime existence REQUIRES a valid RuntimeCertificate

TRACE INTEGRATION RULE:
- Trace may ONLY record admission and legitimacy
- Trace MUST NOT record execution here
- Trace MUST NOT initiate execution
"""

from __future__ import annotations

import os

from afritech.runtime.admission.admission_engine import (
    RuntimeAdmissionEngine,
    AdmissionError,
)

from afritech.trace.trace_engine import TraceEngine
from afritech.trace.trace_context import TraceContext


# ---------------------------------------------------------------------
# Runtime identity
# ---------------------------------------------------------------------

RUNTIME_NAME: str = "afritech.runtime"
RUNTIME_ROLE: str = "EXECUTION_ENTRYPOINT"
RUNTIME_STATUS: str = "GUARDED"


# ---------------------------------------------------------------------
# Certificate configuration
# ---------------------------------------------------------------------

DEFAULT_CERT_PATH: str = (
    "afritech/proof/certificates/runtime_epoch_0006.cert"
)


# ---------------------------------------------------------------------
# Admission enforcement (CRITICAL)
# ---------------------------------------------------------------------

def _admit_runtime(
    cert_path: str = DEFAULT_CERT_PATH,
    trace: TraceEngine | None = None,
) -> None:
    """
    Perform constitutional runtime admission.

    This is the ONLY active responsibility of this module.

    TRACE POLICY:
    - Admission MAY be traced
    - Execution MUST NOT be traced here
    """

    if trace:
        trace.record(
            "runtime_admission_check",
            {"certificate_path": cert_path},
        )

    if not os.path.exists(cert_path):
        if trace:
            trace.complete(
                "runtime_admission_check",
                {"status": "missing_certificate"},
            )
        raise SystemExit(
            f"[AFRITECH:ADMISSION] Missing RuntimeCertificate: {cert_path}"
        )

    try:
        admission = RuntimeAdmissionEngine(cert_path)

        if admission.admit():
            if trace:
                trace.complete(
                    "runtime_admission_check",
                    {"status": "admitted"},
                )
            print("[AFRITECH:ADMISSION] ✅ Runtime admitted under certificate")

    except AdmissionError as e:
        if trace:
            trace.complete(
                "runtime_admission_check",
                {"status": "rejected", "reason": str(e)},
            )
        raise SystemExit(
            f"[AFRITECH:ADMISSION] ❌ Admission failed: {str(e)}"
        )


# ---------------------------------------------------------------------
# Constitutional entry point
# ---------------------------------------------------------------------

def main() -> None:
    """
    Constitutional runtime entry point.

    Responsibilities:
    - Enforce runtime admission (mandatory)
    - Establish constitutional legitimacy
    - Emit TRACE for admission ONLY
    - DO NOT execute business logic
    - DO NOT bypass guards

    Execution MUST occur via guarded runtime mechanisms
    (e.g. guard_executor.py).
    """

    # -------------------------------------------------------------
    # TRACE CONTEXT (ADMISSION SCOPE ONLY)
    # -------------------------------------------------------------

    trace = TraceEngine()

    ctx = TraceContext(
        trace_id="runtime-admission",
        epoch_id="EPOCH_0006",
        request_hash="runtime_boot",
    )

    trace.start(ctx)

    # -------------------------------------------------------------
    # ADMISSION (ONLY ACTION PERMITTED HERE)
    # -------------------------------------------------------------

    _admit_runtime(trace=trace)

    # -------------------------------------------------------------
    # FINALIZE TRACE (ADMISSION LEGITIMACY ONLY)
    # -------------------------------------------------------------

    trace.complete(
        "runtime_entrypoint",
        {"status": "legitimized"},
    )

    trace.finalize()

    # -------------------------------------------------------------
    # IMPORTANT:
    # NO EXECUTION OCCURS HERE.
    #
    # Control MUST be transferred to guarded execution layers
    # such as:
    #
    #   afritech/runtime/guard_executor.py
    #
    # or other constitutionally admitted surfaces.
    # -------------------------------------------------------------

    return


# ---------------------------------------------------------------------
# Direct execution guard
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------
# End of runtime main
# ---------------------------------------------------------------------