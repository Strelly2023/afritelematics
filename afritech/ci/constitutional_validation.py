"""Unified constitutional validation gate for AfriTech.

The module is intentionally boring in the best possible way: one canonical
registry, deterministic ordering, bounded subprocess execution, and fail-closed
registry validation before any validator is invoked.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
FAIL_FAST = True
VALIDATOR_TIMEOUT_SECONDS = 30

PHASE_DEFINITIONS: dict[int, str] = {
    1: "IDENTITY_AND_ALIAS",
    2: "STRUCTURAL_TOPOLOGY",
    3: "AST_AND_EXECUTION_LEGALITY",
    4: "SEMANTIC_AND_INVARIANT_ADMISSIBILITY",
    5: "REPLAY_AND_PROOF_AUTHORITY",
}
EXPECTED_PHASES = frozenset(PHASE_DEFINITIONS)


class ConstitutionalValidationError(Exception):
    """Raised when constitutional validation cannot be admitted."""


@dataclass(frozen=True)
class ValidationSubsystem:
    """Immutable constitutional validator definition."""

    name: str
    module: str
    phase: int
    entrypoint: str = "main"
    required: bool = True
    timeout_seconds: int = VALIDATOR_TIMEOUT_SECONDS

    @property
    def command(self) -> tuple[str, ...]:
        return (sys.executable, "-m", self.module)


@dataclass(frozen=True)
class ValidationResult:
    """Immutable validation execution result."""

    name: str
    phase: int
    success: bool
    duration_seconds: float
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    error: str | None = None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phase": self.phase,
            "success": self.success,
            "duration_seconds": round(self.duration_seconds, 6),
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
        }


SUBSYSTEMS: tuple[ValidationSubsystem, ...] = (
    ValidationSubsystem(name="identity_validator", module="afritech.ci.identity_validator", phase=1),
    ValidationSubsystem(name="alias_validator", module="afritech.ci.alias_validator", phase=1),
    ValidationSubsystem(name="path_ontology_validator", module="afritech.ci.path_ontology_validator", phase=2),
    ValidationSubsystem(name="import_topology_validator", module="afritech.ci.import_topology_validator", phase=2),
    ValidationSubsystem(name="surface_validator", module="afritech.ci.surface_validator", phase=2),
    ValidationSubsystem(name="structural_closure_validator", module="afritech.ci.structural_closure_validator", phase=2),
    ValidationSubsystem(name="ast_import_validator", module="afritech.ci.ast_import_validator", phase=3),
    ValidationSubsystem(name="ast_call_order_validator", module="afritech.ci.ast_call_order_validator", phase=3),
    ValidationSubsystem(name="ast_witness_validator", module="afritech.ci.ast_witness_validator", phase=3),
    ValidationSubsystem(name="execution_integrity_validator", module="afritech.ci.execution_integrity_validator", phase=3),
    ValidationSubsystem(name="semantic_concept_validator", module="afritech.ci.semantic_concept_validator", phase=4),
    ValidationSubsystem(name="cross_concept_validator", module="afritech.ci.cross_concept_validator", phase=4),
    ValidationSubsystem(name="invariant_validator", module="afritech.ci.invariant_validator", phase=4),
    ValidationSubsystem(name="semantic_kernel_validator", module="afritech.ci.semantic_kernel_validator", phase=4),
    ValidationSubsystem(name="adversarial_runner_validator", module="afritech.ci.adversarial_runner_validator", phase=4),
    ValidationSubsystem(name="continuity_validator", module="afritech.ci.continuity_validator", phase=4),
    ValidationSubsystem(name="continuity_resilience_validator", module="afritech.ci.continuity_resilience_validator", phase=4),
    ValidationSubsystem(name="claim_discipline_validator", module="afritech.ci.claim_discipline_validator", phase=4),
    ValidationSubsystem(name="governance_size_validator", module="afritech.ci.governance_size_validator", phase=4),
    ValidationSubsystem(name="semantic_directionality_validator", module="afritech.ci.semantic_directionality_validator", phase=4),
    ValidationSubsystem(name="level2_formal_model_validator", module="afritech.ci.level2_formal_model_validator", phase=4),
    ValidationSubsystem(name="registry_completeness_validator", module="afritech.ci.registry_completeness_validator", phase=4),
    ValidationSubsystem(name="surface_state_resolution_validator", module="afritech.ci.surface_state_resolution_validator", phase=4),
    ValidationSubsystem(name="binding_completeness_validator", module="afritech.ci.binding_completeness_validator", phase=4),
    ValidationSubsystem(name="execution_completeness_validator", module="afritech.ci.execution_completeness_validator", phase=4),
    ValidationSubsystem(name="full_witness_coverage_validator", module="afritech.ci.full_witness_coverage_validator", phase=4),
    ValidationSubsystem(name="formal_runtime_equivalence_validator", module="afritech.ci.formal_runtime_equivalence_validator", phase=4),
    ValidationSubsystem(name="python_gap_validator", module="afritech.ci.python_gap_validator", phase=4),
    ValidationSubsystem(name="yaml_gap_validator", module="afritech.ci.yaml_gap_validator", phase=4),
    ValidationSubsystem(name="partial_planned_audit_validator", module="afritech.ci.partial_planned_audit_validator", phase=4),
    ValidationSubsystem(name="completeness_policy_validator", module="afritech.ci.completeness_policy_validator", phase=4),
    ValidationSubsystem(name="runtime_certificate_validator", module="afritech.ci.runtime_certificate_validator", phase=5),
    ValidationSubsystem(name="witness_validator", module="afritech.ci.witness_validator", phase=5),
    ValidationSubsystem(name="witness_proof_validator", module="afritech.ci.witness_proof_validator", phase=5),
    ValidationSubsystem(name="receipt_validator", module="afritech.ci.receipt_validator", phase=5),
    ValidationSubsystem(name="trace_reconstruction_validator", module="afritech.ci.trace_reconstruction_validator", phase=5),
    ValidationSubsystem(name="execution_lineage_verifier", module="afritech.verify.verify_execution_lineage", phase=5),
    ValidationSubsystem(name="multi_epoch_replay_verifier", module="afritech.verify.verify_multi_epoch_replay", phase=5),
    ValidationSubsystem(name="replay_verifier", module="afritech.verify.replay", phase=5),
    ValidationSubsystem(name="replay_integrity_validator", module="afritech.ci.replay_integrity_validator", phase=5),
    ValidationSubsystem(name="proof_surface_validator", module="afritech.ci.proof_surface_validator", phase=5),
    ValidationSubsystem(name="four_gate_validator", module="afritech.ci.four_gate_validator", phase=5),
    ValidationSubsystem(name="governance_projection_validator", module="afritech.ci.governance_projection_validator", phase=5),
    ValidationSubsystem(name="traceability_bridge_validator", module="afritech.ci.traceability_bridge_validator", phase=5),
    ValidationSubsystem(name="explain_execution_api_validator", module="afritech.ci.explain_execution_api_validator", phase=5),
    ValidationSubsystem(name="projection_enriched_explanation_validator", module="afritech.ci.projection_enriched_explanation_validator", phase=5),
    ValidationSubsystem(name="enforcement_integrity_validator", module="afritech.ci.enforcement_integrity_validator", phase=5),
    ValidationSubsystem(name="afriprogramming_engineering_validator", module="afritech.ci.afriprogramming_engineering_validator", phase=5),
    ValidationSubsystem(name="afripower_intelligence_validator", module="afritech.ci.afripower_intelligence_validator", phase=5),
)


def fail(message: str) -> None:
    raise ConstitutionalValidationError(message)


def sort_key(subsystem: ValidationSubsystem) -> tuple[int, str]:
    return (subsystem.phase, subsystem.name)


def ordered_subsystems(
    subsystems: Iterable[ValidationSubsystem] = SUBSYSTEMS,
) -> tuple[ValidationSubsystem, ...]:
    return tuple(sorted(subsystems, key=sort_key))


def validate_subsystem_registry(
    subsystems: Iterable[ValidationSubsystem] = SUBSYSTEMS,
) -> None:
    names: set[str] = set()
    modules: set[str] = set()
    discovered_phases: set[int] = set()

    for subsystem in subsystems:
        if not subsystem.name.strip():
            fail("subsystem name must not be empty")
        if not subsystem.module.strip():
            fail(f"{subsystem.name} module must not be empty")
        if subsystem.name in names:
            fail(f"duplicate subsystem name detected: {subsystem.name}")
        if subsystem.module in modules:
            fail(f"duplicate subsystem module detected: {subsystem.module}")
        if subsystem.phase not in EXPECTED_PHASES:
            fail(f"invalid phase for {subsystem.name}: {subsystem.phase}")
        if subsystem.timeout_seconds <= 0:
            fail(f"invalid timeout for {subsystem.name}: {subsystem.timeout_seconds}")
        if importlib.util.find_spec(subsystem.module) is None:
            fail(f"subsystem module is not importable: {subsystem.module}")

        names.add(subsystem.name)
        modules.add(subsystem.module)
        discovered_phases.add(subsystem.phase)

    missing = EXPECTED_PHASES - discovered_phases
    if missing:
        fail(f"missing constitutional phases: {sorted(missing)}")


def run_subsystem(subsystem: ValidationSubsystem) -> ValidationResult:
    print(f"Running {subsystem.name}...")
    started = time.perf_counter()

    try:
        completed = subprocess.run(
            list(subsystem.command),
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=subsystem.timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        return ValidationResult(
            name=subsystem.name,
            phase=subsystem.phase,
            success=False,
            duration_seconds=time.perf_counter() - started,
            exit_code=124,
            stdout=_normalize_output(exc.stdout),
            stderr=_normalize_output(exc.stderr),
            error="validator execution timed out",
        )
    except OSError as exc:
        return ValidationResult(
            name=subsystem.name,
            phase=subsystem.phase,
            success=False,
            duration_seconds=time.perf_counter() - started,
            error=f"validator execution error: {exc}",
        )

    duration = time.perf_counter() - started
    success = completed.returncode == 0
    result = ValidationResult(
        name=subsystem.name,
        phase=subsystem.phase,
        success=success,
        duration_seconds=duration,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        error=None if success else f"non-zero exit code: {completed.returncode}",
    )

    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip())
    if success:
        print(f"{subsystem.name} passed ({duration:.4f}s)")

    return result


def run_validation(
    subsystems: Iterable[ValidationSubsystem] = SUBSYSTEMS,
) -> tuple[ValidationResult, ...]:
    subsystem_tuple = tuple(subsystems)
    validate_subsystem_registry(subsystem_tuple)

    print("Starting unified constitutional validation...")
    results: list[ValidationResult] = []
    current_phase: int | None = None

    for subsystem in ordered_subsystems(subsystem_tuple):
        if subsystem.phase != current_phase:
            current_phase = subsystem.phase
            print("=" * 72)
            print(f"PHASE {current_phase}: {PHASE_DEFINITIONS[current_phase]}")
            print("=" * 72)

        result = run_subsystem(subsystem)
        results.append(result)

        if not result.success and subsystem.required:
            print(f"{subsystem.name} failed")
            if result.error:
                print(result.error)
            if FAIL_FAST:
                fail("constitutional validation failed")

    failed = [result for result in results if not result.success]
    if failed:
        fail("one or more constitutional validators failed")

    total_duration = sum(result.duration_seconds for result in results)
    print("=" * 72)
    print("Unified constitutional validation passed")
    print("=" * 72)
    print(f"Validated subsystems: {len(results)}")
    print(f"Total execution time: {total_duration:.4f}s")
    print("Deterministic constitutional closure achieved")

    print("\nRunning classification enforcement...")
    from afritech.ci.classification_ci_validator import (
        run_classification_ci_validation,
    )

    run_classification_ci_validation()

    return tuple(results)


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def main() -> int:
    try:
        run_validation()
        return 0
    except Exception as exc:
        print(f"Constitutional validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
