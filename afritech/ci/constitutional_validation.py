# afritech/ci/constitutional_validation.py

"""
AfriTech Unified Constitutional Validation
==========================================

Single constitutional validation entrypoint.

This validator consolidates all replay-safe,
ontology-safe, and governance-safe constitutional
validation subsystems into one deterministic CI gate.

CONSTITUTIONAL RULE:
No runtime admission, replay admissibility,
or governance transition may occur unless all
constitutional validators succeed.

VALIDATION DOMAINS:
- identity integrity
- alias normalization
- witness admissibility
- invariant consistency
- semantic ontology integrity
- execution surface topology

PHASE 6:
Unified constitutional validation orchestration.
"""

from __future__ import annotations

import importlib
import sys
import traceback

from dataclasses import dataclass
from typing import Callable, List


# ============================================================
# VALIDATION MODEL
# ============================================================

@dataclass(frozen=True)
class ValidationSubsystem:

    name: str

    module: str

    entrypoint: str = "main"


# ============================================================
# REQUIRED CONSTITUTIONAL SUBSYSTEMS
# ============================================================

SUBSYSTEMS: List[
    ValidationSubsystem
] = [

    ValidationSubsystem(
        name="identity_validator",
        module=(
            "afritech.ci."
            "identity_validator"
        ),
    ),

    ValidationSubsystem(
        name="alias_validator",
        module=(
            "afritech.ci."
            "alias_validator"
        ),
    ),

    ValidationSubsystem(
        name="witness_validator",
        module=(
            "afritech.ci."
            "witness_validator"
        ),
    ),

    ValidationSubsystem(
        name="invariant_validator",
        module=(
            "afritech.ci."
            "invariant_validator"
        ),
    ),

    ValidationSubsystem(
        name=(
            "semantic_concept_validator"
        ),
        module=(
            "afritech.ci."
            "semantic_concept_validator"
        ),
    ),

    ValidationSubsystem(
        name="surface_validator",
        module=(
            "afritech.ci."
            "surface_validator"
        ),
    ),
]


# ============================================================
# FAILURE
# ============================================================

class ConstitutionalValidationError(
    Exception
):
    pass


def fail(message: str) -> None:

    raise ConstitutionalValidationError(
        message
    )


# ============================================================
# IMPORT VALIDATION
# ============================================================

def load_entrypoint(
    subsystem: ValidationSubsystem,
) -> Callable[[], int]:

    try:

        module = importlib.import_module(
            subsystem.module
        )

    except Exception as exc:

        fail(
            f"failed to import "
            f"{subsystem.name}: {exc}"
        )

    if not hasattr(
        module,
        subsystem.entrypoint,
    ):

        fail(
            f"{subsystem.name} missing "
            f"entrypoint: "
            f"{subsystem.entrypoint}"
        )

    entrypoint = getattr(
        module,
        subsystem.entrypoint,
    )

    if not callable(
        entrypoint
    ):

        fail(
            f"{subsystem.name} entrypoint "
            f"is not callable"
        )

    return entrypoint


# ============================================================
# EXECUTION
# ============================================================

def run_subsystem(
    subsystem: ValidationSubsystem,
) -> None:

    print(
        f"🔍 Running "
        f"{subsystem.name}..."
    )

    entrypoint = load_entrypoint(
        subsystem
    )

    try:

        result = entrypoint()

    except SystemExit as exc:

        code = exc.code

        if code not in (0, None):

            fail(
                f"{subsystem.name} exited "
                f"with code {code}"
            )

        return

    except Exception:

        traceback.print_exc()

        fail(
            f"{subsystem.name} raised "
            f"unexpected exception"
        )

    if result not in (0, None):

        fail(
            f"{subsystem.name} returned "
            f"non-zero result: {result}"
        )


# ============================================================
# ORCHESTRATION
# ============================================================

def run_validation() -> None:

    print(
        "🚀 Starting unified "
        "constitutional validation..."
    )

    print()

    for subsystem in SUBSYSTEMS:

        run_subsystem(
            subsystem
        )

        print()

    print(
        "✅ Unified constitutional "
        "validation passed"
    )

    print(
        "✅ Identity integrity verified"
    )

    print(
        "✅ Alias normalization verified"
    )

    print(
        "✅ Witness admissibility verified"
    )

    print(
        "✅ Invariant consistency verified"
    )

    print(
        "✅ Semantic ontology integrity "
        "verified"
    )

    print(
        "✅ Execution surface topology "
        "verified"
    )

    print(
        "✅ Replay-safe constitutional "
        "governance verified"
    )


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:

    try:

        run_validation()

        return 0

    except Exception as exc:

        print(
            f"❌ Constitutional validation "
            f"failed: {exc}"
        )

        return 1


if __name__ == "__main__":

    sys.exit(main())