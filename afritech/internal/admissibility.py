# afritech/internal/admissibility.py

"""
AfriTech Internal Admissibility Guards
=====================================

This module enforces RUNTIME admissibility of internal
mutation-capable code.

It prevents constitutional bypass via:
- direct imports
- illicit invocation paths
- accidental misuse of internal mutation APIs

RULE:
Any internal mutation logic MUST prove that it was invoked
by the constitutional gateway.

Failure to do so is a CONSTITUTIONAL VIOLATION.
"""

from __future__ import annotations

import inspect

from afritech.guards.engine import ConstitutionalViolation


# ---------------------------------------------------------------------
# ADMISSIBLE CALLERS (CANONICAL)
# ---------------------------------------------------------------------

# Any module under this prefix is considered constitutionally admissible
# (allows refactoring inside the gateway namespace without breakage)
_ALLOWED_CALLER_PREFIXES = (
    "afritech.kernel.constitutional_gateway",
)


# ---------------------------------------------------------------------
# ADMISSIBILITY ENFORCEMENT
# ---------------------------------------------------------------------

def assert_caller_is_constitutional_gateway() -> None:
    """
    Enforce that the call stack includes the constitutional gateway.

    This function MUST be invoked at the top of every
    mutation-capable internal function.

    Enforcement properties:
    - fail-closed
    - runtime-enforced
    - topology-based (not policy-based)

    If this assertion fails, execution MUST halt immediately.
    """

    # Inspect a bounded portion of the stack for performance and clarity
    stack = inspect.stack(context=0)

    try:
        # Skip the current frame (this function)
        for frame_info in stack[1:]:
            module = inspect.getmodule(frame_info.frame)

            if module is None:
                continue

            module_name = getattr(module, "__name__", "")

            # Check admissible prefixes
            for prefix in _ALLOWED_CALLER_PREFIXES:
                if module_name.startswith(prefix):
                    return  # ✅ admissible call path

        # ❌ No admissible caller found
        raise ConstitutionalViolation(
            "ILLEGAL_MUTATION_CALLER: "
            "internal mutation invoked outside constitutional gateway"
        )

    finally:
        # Prevent reference cycles and memory retention
        del stack