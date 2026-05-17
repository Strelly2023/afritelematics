# afritech/runtime/afriride_runtime_enforcement.py

"""
AfriRide Runtime Constitutional Enforcement Declaration
=======================================================

Purpose:
Declare, at the constitutional layer, which AfriTech invariants
are enforced by the AfriRide deterministic runtime.

This module:
- contains NO executable logic
- performs NO runtime actions
- imports NO application code
- exists ONLY to make enforcement visible to the constitution

It acts as a governance bridge between:
- afritech/ (constitutional authority)
- ecosystems/afriride/ (governed application runtime)

This file is REQUIRED for semantic coverage verification.
"""

from afritech.constitution.compiled.invariants_index import (
    I4_DETERMINISTIC_RUNTIME,
    I5_EPOCH_MONOTONIC,
    I6_CLOSED_EXECUTION_WORLD,
)

# ---------------------------------------------------------------------
# CONSTITUTIONAL ENFORCEMENT DECLARATION
# ---------------------------------------------------------------------

ENFORCED_INVARIANTS = {
    I4_DETERMINISTIC_RUNTIME,
    I5_EPOCH_MONOTONIC,
    I6_CLOSED_EXECUTION_WORLD,
}

# ---------------------------------------------------------------------
# GOVERNANCE NOTES (NON-EXECUTABLE)
# ---------------------------------------------------------------------
#
# - Enforcement is implemented in:
#     ecosystems/afriride/runtime/execution/deterministic_executor.py
#
# - This file exists ONLY to declare constitutional responsibility.
#
# - The AfriTech constitution does NOT inspect ecosystem code directly.
#
# - Removal or modification of this file requires:
#     - ADR approval
#     - epoch advancement
#     - registry reseal
#
# ---------------------------------------------------------------------
