# afritech/ci/constitutional_validation.py

"""
AfriTech Unified Constitutional Validation
==========================================

PHASE 8:
Deterministic Constitutional Admission Kernel

This module defines the single authoritative
constitutional validation gate for the AfriTech
ecosystem.

No:
- runtime admission
- governance transition
- replay certification
- ontology activation
- semantic expansion
- execution authorization

may occur unless ALL required constitutional
validators succeed.

CONSTITUTIONAL GUARANTEES
-------------------------
This validator enforces:

- deterministic execution ordering
- replay-safe orchestration
- ontology-safe subsystem loading
- constitutional dependency closure
- semantic admissibility
- invariant preservation
- execution surface integrity
- bounded validator execution
- governance-safe validation sequencing
- replay-bound legitimacy enforcement

VALIDATION DOMAINS
------------------
- identity integrity
- alias normalization
- witness admissibility
- invariant consistency
- semantic ontology integrity
- execution surface topology
- runtime certificate validity
- AST semantic admissibility
- replay verification
- import topology legality
- path ontology legality

ARCHITECTURAL PROPERTY
----------------------
This file acts as the constitutional admission
controller for the AfriTech verification runtime.

FORMAL MODEL
-------------
admit(state) :=
    forall validator:
        validator.valid(state)

Only replay-verifiable system states may
be constitutionally admitted.
"""

from __future__ import annotations

import importlib
import multiprocessing
import sys
import time
import traceback

from dataclasses import dataclass

from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Set


# ============================================================
# CONSTITUTIONAL CONSTANTS
# ============================================================

FAIL_FAST = True

VALID_RESULT_CODES = {
    0,
    None,
}

VALIDATOR_TIMEOUT_SECONDS = 10


# ============================================================
# PHASE DEFINITIONS
# ============================================================

PHASE_DEFINITIONS: Dict[int, str] = {

    1: "IDENTITY_AND_ALIAS",

    2: "STRUCTURAL_TOPOLOGY",

    3: "AST_AND_EXECUTION_LEGALITY",

    4: (
        "SEMANTIC_AND_"
        "INVARIANT_ADMISSIBILITY"
    ),

    5: "REPLAY_AND_PROOF_AUTHORITY",
}


EXPECTED_PHASES: Set[int] = set(
    PHASE_DEFINITIONS.keys()
)

# ============================================================
# FAILURE
# ============================================================

class ConstitutionalValidationError(
    Exception
):
    """
    Raised when constitutional validation
    fails.
    """
    pass


def fail(message: str) -> None:

    raise ConstitutionalValidationError(
        message
    )


# ============================================================
# VALIDATION SUBSYSTEM
# ============================================================

@dataclass(frozen=True)
class ValidationSubsystem:
    """
    Immutable constitutional validator
    definition.
    """

    name: str

    module: str

    entrypoint: str = "main"

    phase: int = 0

    required: bool = True


# ============================================================
# VALIDATION RESULT
# ============================================================

@dataclass(frozen=True)
class ValidationResult:
    """
    Immutable validation execution result.
    """

    name: str

    phase: int

    success: bool

    duration_seconds: float

    error: Optional[str] = None


# ============================================================
# CONSTITUTIONAL SUBSYSTEMS
# ============================================================

SUBSYSTEMS: List[
    ValidationSubsystem
] = [

    # ========================================================
    # PHASE 1
    # IDENTITY + ALIAS
    # ========================================================

    ValidationSubsystem(
        name="identity_validator",
        module=(
            "afritech.ci."
            "identity_validator"
        ),
        phase=1,
    ),

    ValidationSubsystem(
        name="alias_validator",
        module=(
            "afritech.ci."
            "alias_validator"
        ),
        phase=1,
    ),

    # ========================================================
    # PHASE 2
    # STRUCTURAL TOPOLOGY
    # ========================================================

    ValidationSubsystem(
        name="path_ontology_validator",
        module=(
            "afritech.ci."
            "path_ontology_validator"
        ),
        phase=2,
    ),

    ValidationSubsystem(
        name="import_topology_validator",
        module=(
            "afritech.ci."
            "import_topology_validator"
        ),
        phase=2,
    ),

    ValidationSubsystem(
        name="surface_validator",
        module=(
            "afritech.ci."
            "surface_validator"
        ),
        phase=2,
    ),

    # ========================================================
    # PHASE 3
    # AST + EXECUTION LEGALITY
    # ========================================================

    ValidationSubsystem(
        name="ast_import_validator",
        module=(
            "afritech.ci."
            "ast_import_validator"
        ),
        phase=3,
    ),

    ValidationSubsystem(
        name="ast_call_order_validator",
        module=(
            "afritech.ci."
            "ast_call_order_validator"
        ),
        phase=3,
    ),

    ValidationSubsystem(
        name="ast_witness_validator",
        module=(
            "afritech.ci."
            "ast_witness_validator"
        ),
        phase=3,
    ),

    # ========================================================
    # PHASE 4
    # SEMANTIC + INVARIANT ADMISSIBILITY
    # ========================================================

    ValidationSubsystem(
        name="semantic_concept_validator",
        module=(
            "afritech.ci."
            "semantic_concept_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="cross_concept_validator",
        module=(
            "afritech.ci."
            "cross_concept_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="invariant_validator",
        module=(
            "afritech.ci."
            "invariant_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="semantic_kernel_validator",
        module=(
            "afritech.ci."
            "semantic_kernel_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="adversarial_runner_validator",
        module=(
            "afritech.ci."
            "adversarial_runner_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="governance_size_validator",
        module=(
            "afritech.ci."
            "governance_size_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="semantic_directionality_validator",
        module=(
            "afritech.ci."
            "semantic_directionality_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="level2_formal_model_validator",
        module=(
            "afritech.ci."
            "level2_formal_model_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="registry_completeness_validator",
        module=(
            "afritech.ci."
            "registry_completeness_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="surface_state_resolution_validator",
        module=(
            "afritech.ci."
            "surface_state_resolution_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="binding_completeness_validator",
        module=(
            "afritech.ci."
            "binding_completeness_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="execution_completeness_validator",
        module=(
            "afritech.ci."
            "execution_completeness_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="full_witness_coverage_validator",
        module=(
            "afritech.ci."
            "full_witness_coverage_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="formal_runtime_equivalence_validator",
        module=(
            "afritech.ci."
            "formal_runtime_equivalence_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="python_gap_validator",
        module=(
            "afritech.ci."
            "python_gap_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="yaml_gap_validator",
        module=(
            "afritech.ci."
            "yaml_gap_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="partial_planned_audit_validator",
        module=(
            "afritech.ci."
            "partial_planned_audit_validator"
        ),
        phase=4,
    ),

    ValidationSubsystem(
        name="completeness_policy_validator",
        module=(
            "afritech.ci."
            "completeness_policy_validator"
        ),
        phase=4,
    ),

    # ========================================================
    # PHASE 5
    # REPLAY + PROOF AUTHORITY
    # ========================================================

    ValidationSubsystem(
        name="runtime_certificate_validator",
        module=(
            "afritech.ci."
            "runtime_certificate_validator"
        ),
        phase=5,
    ),

    ValidationSubsystem(
        name="witness_validator",
        module=(
            "afritech.ci."
            "witness_validator"
        ),
        phase=5,
    ),

    ValidationSubsystem(
        name="receipt_validator",
        module=(
            "afritech.ci."
            "receipt_validator"
        ),
        phase=5,
    ),

    ValidationSubsystem(
        name="trace_reconstruction_validator",
        module=(
            "afritech.ci."
            "trace_reconstruction_validator"
        ),
        phase=5,
    ),

    ValidationSubsystem(
        name="execution_lineage_verifier",
        module=(
            "afritech.verify."
            "verify_execution_lineage"
        ),
        phase=5,
    ),

    ValidationSubsystem(
        name="multi_epoch_replay_verifier",
        module=(
            "afritech.verify."
            "verify_multi_epoch_replay"
        ),
        phase=5,
    ),

    ValidationSubsystem(
        name="replay_verifier",
        module=(
            "afritech.verify.replay"
        ),
        phase=5,
    ),
]


# ============================================================
# SORTING
# ============================================================

def sort_key(
    subsystem: ValidationSubsystem,
):

    replay_priority = (
        subsystem.name
        == "replay_verifier"
    )

    return (
        subsystem.phase,
        replay_priority,
        subsystem.name,
    )


# ============================================================
# REGISTRY VALIDATION
# ============================================================

def validate_subsystem_registry() -> None:
    """
    Ensure deterministic constitutional
    subsystem registry integrity.
    """

    names = set()

    modules = set()

    for subsystem in SUBSYSTEMS:

        if subsystem.name in names:

            fail(
                f"duplicate subsystem "
                f"name detected: "
                f"{subsystem.name}"
            )

        if subsystem.module in modules:

            fail(
                f"duplicate subsystem "
                f"module detected: "
                f"{subsystem.module}"
            )

        if subsystem.phase not in (
            PHASE_DEFINITIONS
        ):

            fail(
                f"invalid phase for "
                f"{subsystem.name}: "
                f"{subsystem.phase}"
            )

        names.add(
            subsystem.name
        )

        modules.add(
            subsystem.module
        )


# ============================================================
# PHASE VALIDATION
# ============================================================

def validate_phase_coverage() -> None:
    """
    Ensure complete constitutional
    phase coverage.
    """

    discovered = {
        subsystem.phase
        for subsystem in SUBSYSTEMS
    }

    missing = (
        EXPECTED_PHASES
        - discovered
    )

    unknown = (
        discovered
        - EXPECTED_PHASES
    )

    if missing:

        fail(
            f"missing constitutional "
            f"phases: "
            f"{sorted(missing)}"
        )

    if unknown:

        fail(
            f"unknown constitutional "
            f"phases: "
            f"{sorted(unknown)}"
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
# SUBPROCESS EXECUTION
# ============================================================

def execute_entrypoint(
    entrypoint,
    queue,
) -> None:

    try:

        result = entrypoint()

        queue.put(
            (
                "success",
                result,
            )
        )

    except SystemExit as exc:
        # ✅ CRITICAL FIX: handle sys.exit()
        queue.put(
            (
                "success",
                exc.code,
            )
        )

    except BaseException:
        # ✅ catch ALL remaining failures (not just Exception)
        queue.put(
            (
                "failure",
                traceback.format_exc(),
            )
        )

# ============================================================
# SUBSYSTEM EXECUTION
# ============================================================

def run_subsystem(
    subsystem: ValidationSubsystem,
) -> ValidationResult:

    print(
        f"🔍 Running "
        f"{subsystem.name}..."
    )

    started = time.perf_counter()

    try:

        entrypoint = load_entrypoint(
            subsystem
        )

        queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=execute_entrypoint,
            args=(
                entrypoint,
                queue,
            ),
        )

        process.start()

        process.join(
            VALIDATOR_TIMEOUT_SECONDS
        )

        if process.is_alive():

            process.terminate()

            process.join()

            duration = (
                time.perf_counter()
                - started
            )

            return ValidationResult(
                name=subsystem.name,
                phase=subsystem.phase,
                success=False,
                duration_seconds=duration,
                error=(
                    "validator execution "
                    "timed out"
                ),
            )

        duration = (
            time.perf_counter()
            - started
        )

        try:

            status, payload = (
                queue.get_nowait()
            )

        except Exception:

            return ValidationResult(
                name=subsystem.name,
                phase=subsystem.phase,
                success=False,
                duration_seconds=duration,
                error=(
                    "validator produced "
                    "no execution result"
                ),
            )

        if status == "failure":

            return ValidationResult(
                name=subsystem.name,
                phase=subsystem.phase,
                success=False,
                duration_seconds=duration,
                error=payload,
            )

        if payload not in (
            VALID_RESULT_CODES
        ):

            return ValidationResult(
                name=subsystem.name,
                phase=subsystem.phase,
                success=False,
                duration_seconds=duration,
                error=(
                    f"non-zero result: "
                    f"{payload}"
                ),
            )

        print(
            f"✅ {subsystem.name} "
            f"passed "
            f"({duration:.4f}s)"
        )

        return ValidationResult(
            name=subsystem.name,
            phase=subsystem.phase,
            success=True,
            duration_seconds=duration,
        )

    except Exception:

        traceback.print_exc()

        duration = (
            time.perf_counter()
            - started
        )

        return ValidationResult(
            name=subsystem.name,
            phase=subsystem.phase,
            success=False,
            duration_seconds=duration,
            error=(
                "unexpected "
                "execution failure"
            ),
        )


# ============================================================
# ORCHESTRATION
# ============================================================

def run_validation() -> None:

    validate_subsystem_registry()

    validate_phase_coverage()

    print(
        "🚀 Starting unified "
        "constitutional validation..."
    )

    print()

    results: List[
        ValidationResult
    ] = []

    ordered_subsystems = sorted(
        SUBSYSTEMS,
        key=sort_key,
    )

    current_phase = None

    for subsystem in ordered_subsystems:

        if subsystem.phase != current_phase:

            current_phase = subsystem.phase

            phase_name = (
                PHASE_DEFINITIONS[
                    current_phase
                ]
            )

            print(
                "=" * 72
            )

            print(
                f"PHASE "
                f"{current_phase}: "
                f"{phase_name}"
            )

            print(
                "=" * 72
            )

        result = run_subsystem(
            subsystem
        )

        results.append(
            result
        )

        if (
            not result.success
            and subsystem.required
        ):

            print()

            print(
                f"❌ "
                f"{subsystem.name} failed"
            )

            print(
                f"Reason:"
            )

            print(
                result.error
            )

            if FAIL_FAST:

                fail(
                    "constitutional "
                    "validation failed"
                )

        print()

    failed = [
        result
        for result in results
        if not result.success
    ]

    if failed:

        print(
            "❌ Constitutional "
            "validation failed"
        )

        print()

        for result in failed:

            phase_name = (
                PHASE_DEFINITIONS[
                    result.phase
                ]
            )

            print(
                f"[PHASE "
                f"{result.phase} - "
                f"{phase_name}] "
                f"{result.name}"
            )

            print(
                f"{result.error}"
            )

            print()

        fail(
            "one or more constitutional "
            "validators failed"
        )

    total_duration = sum(
        result.duration_seconds
        for result in results
    )

    print(
        "=" * 72
    )

    print(
        "✅ Unified constitutional "
        "validation passed"
    )

    print(
        "=" * 72
    )

    print(
        f"Validated subsystems: "
        f"{len(results)}"
    )

    print(
        f"Total execution time: "
        f"{total_duration:.4f}s"
    )

    print()

    for phase_id in sorted(
        PHASE_DEFINITIONS
    ):

        print(
            f"✅ PHASE "
            f"{phase_id}: "
            f"{PHASE_DEFINITIONS[phase_id]}"
        )

    print()

    print(
        "✅ Identity integrity verified"
    )

    print(
        "✅ Alias normalization verified"
    )

    print(
        "✅ Structural topology verified"
    )

    print(
        "✅ AST legality verified"
    )

    print(
        "✅ Semantic ontology integrity "
        "verified"
    )

    print(
        "✅ Witness admissibility verified"
    )

    print(
        "✅ Runtime certificate integrity "
        "verified"
    )

    print(
        "✅ Replay authority verified"
    )

    print(
        "✅ Replay-safe constitutional "
        "governance verified"
    )

    print(
        "✅ Deterministic constitutional "
        "closure achieved"
    )


# ============================================================
# ENTRYPOINT
# ============================================================

def main() -> int:

    try:

        run_validation()

        return 0

    except Exception as exc:

        print()

        print(
            f"❌ Constitutional "
            f"validation failed: "
            f"{exc}"
        )

        return 1


if __name__ == "__main__":

    multiprocessing.freeze_support()

    sys.exit(main())
