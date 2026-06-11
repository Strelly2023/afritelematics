"""Canonical AfriTech constitutional CI pipeline.

The pipeline is the CI admissibility gate. It validates its own registry before
running, executes bounded subprocesses, and refuses duplicate or malformed
steps.
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STEP_TIMEOUT_SECONDS = 180


class ConstitutionalPipelineError(Exception):
    """Raised when the constitutional pipeline cannot be admitted."""


@dataclass(frozen=True)
class PipelineStep:
    name: str
    command: tuple[str, ...]
    phase: str
    timeout_seconds: int = DEFAULT_STEP_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ConstitutionalPipelineError("pipeline step name must not be empty")
        if not self.phase.strip():
            raise ConstitutionalPipelineError(f"{self.name} phase must not be empty")
        if len(self.command) < 3:
            raise ConstitutionalPipelineError(f"{self.name} command is incomplete")


@dataclass(frozen=True)
class StepResult:
    name: str
    phase: str
    success: bool
    exit_code: int | None
    elapsed_seconds: float
    stdout: str = ""
    stderr: str = ""
    error: str | None = None

    def canonical_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "phase": self.phase,
            "success": self.success,
            "exit_code": self.exit_code,
            "elapsed_seconds": round(self.elapsed_seconds, 6),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
        }


@dataclass(frozen=True)
class PipelineResult:
    completed: int
    failed_step: str | None
    elapsed_seconds: float
    deterministic: bool = True


def module_step(name: str, module: str, phase: str) -> PipelineStep:
    return PipelineStep(
        name=name,
        phase=phase,
        command=(sys.executable, "-m", module),
    )


def compileall_step() -> PipelineStep:
    return PipelineStep(
        name="compileall_afritech",
        phase="STATIC",
        command=(sys.executable, "-m", "compileall", "afritech"),
    )


YAML_TARGETS: tuple[str, ...] = (
    "afritech/constitution/INVARIANTS.yaml",
    "afritech/constitution/invariants_semantics.yaml",
    "afritech/constitution/semantic_atoms_core.yaml",
    "afritech/constitution/semantic_atoms.yaml",
    "afritech/constitution/profiles.yaml",
    "afritech/constitution/evolution/amendments.yaml",
    "afritech/constitution/evolution/epochs.yaml",
    "afritech/simulation/adversarial/index.yaml",
    "afritech/ci/semantic_integrity_checks.yaml",
    "afritech/ci/governance_size_policy.yaml",
    "afritech/core/runtime/policies/replay_compression.yaml",
    "afritech/core/runtime/contracts/witness_recovery_contract.yaml",
    "afritech/proof/witness/WITNESS_REGISTRY.yaml",
    "afritech/constitution/level2_formal_model.yaml",
    "afritech/constitution/CONTINUITY_PROFILE.yaml",
    "afritech/constitution/CLAIM_DISCIPLINE.yaml",
    "afritech/constitution/FIVE_INVARIANT_CONTRACT.yaml",
    "afritech/ci/execution_completion_matrix.yaml",
    "afritech/ci/completeness_policy.yaml",
    "afritech/architecture/implementation_registry.yaml",
    "afritech/architecture/surface_implementation_binding.yaml",
    "afritech/architecture/enforcement_matrix.yaml",
    "afritech/architecture/surface_authority_registry.yaml",
    "afritech/epoch/epoch_registry.yaml",
    "afritech/governance/binding_manifest.yaml",
    "afritech/simulation/continuity/index.yaml",
)


PIPELINE: tuple[PipelineStep, ...] = (
    PipelineStep(
        name="compile_invariants",
        phase="CONSTITUTION",
        command=(
            sys.executable,
            "-m",
            "afritech.constitution.compiler.compile_invariants",
            "--execution",
            "afritech/constitution/INVARIANTS.yaml",
            "--semantics",
            "afritech/constitution/invariants_semantics.yaml",
            "--out",
            "afritech/constitution/compiled/invariants_ir.json",
        ),
    ),
    module_step("verify_semantic_coverage", "afritech.constitution.verify_semantic_coverage", "CONSTITUTION"),
    module_step("semantic_kernel_validator", "afritech.ci.semantic_kernel_validator", "CONSTITUTION"),
    module_step("structural_closure_validator", "afritech.ci.structural_closure_validator", "CONSTITUTION"),
    module_step("adversarial_runner_validator", "afritech.ci.adversarial_runner_validator", "CONSTITUTION"),
    module_step("continuity_validator", "afritech.ci.continuity_validator", "CONSTITUTION"),
    module_step("continuity_resilience_validator", "afritech.ci.continuity_resilience_validator", "CONSTITUTION"),
    module_step("claim_discipline_validator", "afritech.ci.claim_discipline_validator", "CONSTITUTION"),
    module_step("semantic_directionality_validator", "afritech.ci.semantic_directionality_validator", "CONSTITUTION"),
    module_step("governance_size_validator", "afritech.ci.governance_size_validator", "CONSTITUTION"),
    module_step("witness_proof_validator", "afritech.ci.witness_proof_validator", "CONSTITUTION"),
    module_step("receipt_validator", "afritech.ci.receipt_validator", "CONSTITUTION"),
    module_step("trace_reconstruction_validator", "afritech.ci.trace_reconstruction_validator", "CONSTITUTION"),
    module_step("replay_integrity_validator", "afritech.ci.replay_integrity_validator", "CONSTITUTION"),
    module_step("level2_formal_model_validator", "afritech.ci.level2_formal_model_validator", "CONSTITUTION"),
    module_step("registry_completeness_validator", "afritech.ci.registry_completeness_validator", "CONSTITUTION"),
    module_step("surface_state_resolution_validator", "afritech.ci.surface_state_resolution_validator", "CONSTITUTION"),
    module_step("binding_completeness_validator", "afritech.ci.binding_completeness_validator", "CONSTITUTION"),
    module_step("execution_completeness_validator", "afritech.ci.execution_completeness_validator", "CONSTITUTION"),
    module_step("full_witness_coverage_validator", "afritech.ci.full_witness_coverage_validator", "CONSTITUTION"),
    module_step("formal_runtime_equivalence_validator", "afritech.ci.formal_runtime_equivalence_validator", "CONSTITUTION"),
    module_step("python_gap_validator", "afritech.ci.python_gap_validator", "CONSTITUTION"),
    module_step("yaml_gap_validator", "afritech.ci.yaml_gap_validator", "CONSTITUTION"),
    module_step("partial_planned_audit_validator", "afritech.ci.partial_planned_audit_validator", "CONSTITUTION"),
    module_step("completeness_policy_validator", "afritech.ci.completeness_policy_validator", "CONSTITUTION"),
    module_step("verify_execution_lineage", "afritech.verify.verify_execution_lineage", "CONSTITUTION"),
    module_step("verify_multi_epoch_replay", "afritech.verify.verify_multi_epoch_replay", "CONSTITUTION"),
    module_step("generate_completeness", "afritech.proof.generate_completeness", "CONSTITUTION"),
    module_step("ast_import_validator", "afritech.ci.ast_import_validator", "STATIC"),
    module_step(
        "guard_runtime_boundary_governance",
        "afritech.guards.guard_runtime_boundary_governance",
        "STATIC",
    ),
    module_step("execution_integrity_validator", "afritech.ci.execution_integrity_validator", "STATIC"),
    module_step("proof_surface_validator", "afritech.ci.proof_surface_validator", "STATIC"),
    PipelineStep(
        name="four_gate_validator",
        phase="STATIC",
        command=(sys.executable, "-m", "afritech.ci.four_gate_validator"),
    ),
    module_step("governance_projection_validator", "afritech.ci.governance_projection_validator", "STATIC"),
    module_step("traceability_bridge_validator", "afritech.ci.traceability_bridge_validator", "STATIC"),
    module_step("explain_execution_api_validator", "afritech.ci.explain_execution_api_validator", "STATIC"),
    module_step("projection_enriched_explanation_validator", "afritech.ci.projection_enriched_explanation_validator", "STATIC"),
    module_step("afriprogramming_engineering_validator", "afritech.ci.afriprogramming_engineering_validator", "STATIC"),
    module_step("afripower_intelligence_validator", "afritech.ci.afripower_intelligence_validator", "STATIC"),
    module_step(
        "afriride_controlled_pilot_layer_validator",
        "afritech.ci.afriride_controlled_pilot_layer_validator",
        "STATIC",
    ),
    module_step(
        "afriride_controlled_pilot_scenario_matrix_validator",
        "afritech.ci.afriride_controlled_pilot_scenario_matrix_validator",
        "STATIC",
    ),
    module_step(
        "afriride_controlled_pilot_runbook_validator",
        "afritech.ci.afriride_controlled_pilot_runbook_validator",
        "STATIC",
    ),
    module_step(
        "afriride_controlled_pilot_evidence_bundle_validator",
        "afritech.ci.afriride_controlled_pilot_evidence_bundle_validator",
        "STATIC",
    ),
    module_step(
        "afriride_evidence_origin_control_validator",
        "afritech.ci.afriride_evidence_origin_control_validator",
        "STATIC",
    ),
    module_step(
        "afriride_ga_elite_pilot_rollout_strategy_validator",
        "afritech.ci.afriride_ga_elite_pilot_rollout_strategy_validator",
        "STATIC",
    ),
    module_step(
        "afriride_execution_grade_pilot_system_validator",
        "afritech.ci.afriride_execution_grade_pilot_system_validator",
        "STATIC",
    ),
    module_step(
        "afriride_field_execution_transition_boundary_validator",
        "afritech.ci.afriride_field_execution_transition_boundary_validator",
        "STATIC",
    ),
    module_step(
        "afriride_controlled_pilot_execution_receipt_validator",
        "afritech.ci.afriride_controlled_pilot_execution_receipt_validator",
        "STATIC",
    ),
    module_step(
        "afriride_controlled_pilot_evidence_automation_validator",
        "afritech.ci.afriride_controlled_pilot_evidence_automation_validator",
        "STATIC",
    ),
    module_step(
        "afriride_controlled_pilot_certification_validator",
        "afritech.ci.afriride_controlled_pilot_certification_validator",
        "STATIC",
    ),
    module_step(
        "afriride_wave7_go_no_go_gate_validator",
        "afritech.ci.afriride_wave7_go_no_go_gate_validator",
        "STATIC",
    ),
    module_step(
        "afriride_pilot_metrics_dashboard_validator",
        "afritech.ci.afriride_pilot_metrics_dashboard_validator",
        "STATIC",
    ),
    module_step(
        "afriride_wave6_execution_checkpoint_validator",
        "afritech.ci.afriride_wave6_execution_checkpoint_validator",
        "STATIC",
    ),
    module_step(
        "afriride_pilot_execution_checklist_validator",
        "afritech.ci.afriride_pilot_execution_checklist_validator",
        "STATIC",
    ),
    module_step(
        "afriride_melbourne_phase_execution_control_validator",
        "afritech.ci.afriride_melbourne_phase_execution_control_validator",
        "STATIC",
    ),
    module_step(
        "afriride_bujumbura_uvira_phase_execution_control_validator",
        "afritech.ci.afriride_bujumbura_uvira_phase_execution_control_validator",
        "STATIC",
    ),
    module_step(
        "afriride_kinshasa_phase_execution_control_validator",
        "afritech.ci.afriride_kinshasa_phase_execution_control_validator",
        "STATIC",
    ),
    module_step(
        "afriride_global_validation_phase_execution_control_validator",
        "afritech.ci.afriride_global_validation_phase_execution_control_validator",
        "STATIC",
    ),
    PipelineStep(
        name="enforcement_integrity_validator",
        phase="STATIC",
        command=(sys.executable, "-m", "afritech.ci.enforcement_integrity_validator"),
    ),
    compileall_step(),
)


def banner(title: str) -> None:
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def validate_yaml_documents(
    targets: Iterable[str] = YAML_TARGETS,
) -> None:
    banner("PHASE 0: YAML VALIDATION")

    for path in targets:
        target = ROOT / path
        if not target.exists():
            raise ConstitutionalPipelineError(f"Missing file: {path}")
        try:
            yaml.safe_load(target.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ConstitutionalPipelineError(f"Invalid YAML {path}: {exc}") from exc
        print(f"YAML OK: {path}")


def validate_pipeline_registry(
    steps: Iterable[PipelineStep] = PIPELINE,
) -> None:
    names: set[str] = set()
    commands: set[tuple[str, ...]] = set()
    phases: list[str] = []
    phase_order = {"CONSTITUTION": 0, "STATIC": 1}

    for step in steps:
        if step.name in names:
            raise ConstitutionalPipelineError(f"duplicate pipeline step name: {step.name}")
        if step.command in commands:
            raise ConstitutionalPipelineError(f"duplicate pipeline command: {' '.join(step.command)}")
        if step.timeout_seconds <= 0:
            raise ConstitutionalPipelineError(f"invalid timeout for step: {step.name}")
        if step.phase not in phase_order:
            raise ConstitutionalPipelineError(f"unknown pipeline phase: {step.phase}")
        if step.command[1:3] != ("-m", "compileall") and "-m" not in step.command:
            raise ConstitutionalPipelineError(f"step must execute a Python module: {step.name}")

        names.add(step.name)
        commands.add(step.command)
        phases.append(step.phase)

    if phases != sorted(phases, key=lambda phase: phase_order[phase]):
        raise ConstitutionalPipelineError("pipeline phases are not grouped deterministically")


def run_step(step: PipelineStep) -> StepResult:
    print(f"Running {step.name}...")
    start = time.perf_counter()

    try:
        completed = subprocess.run(
            list(step.command),
            cwd=ROOT,
            text=True,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=step.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return StepResult(
            name=step.name,
            phase=step.phase,
            success=False,
            exit_code=124,
            elapsed_seconds=time.perf_counter() - start,
            stdout=_normalize_output(exc.stdout),
            stderr=_normalize_output(exc.stderr),
            error="pipeline step timed out",
        )
    except OSError as exc:
        return StepResult(
            name=step.name,
            phase=step.phase,
            success=False,
            exit_code=None,
            elapsed_seconds=time.perf_counter() - start,
            error=f"pipeline step execution error: {exc}",
        )

    elapsed = time.perf_counter() - start
    success = completed.returncode == 0
    result = StepResult(
        name=step.name,
        phase=step.phase,
        success=success,
        exit_code=completed.returncode,
        elapsed_seconds=elapsed,
        stdout=completed.stdout,
        stderr=completed.stderr,
        error=None if success else f"non-zero exit code: {completed.returncode}",
    )

    if completed.stdout:
        print(completed.stdout.strip())
    if completed.stderr:
        print(completed.stderr.strip())
    if success:
        print(f"{step.name} passed ({elapsed:.4f}s)")

    return result


def execute_pipeline(
    steps: Iterable[PipelineStep] = PIPELINE,
) -> PipelineResult:
    step_tuple = tuple(steps)
    validate_pipeline_registry(step_tuple)
    validate_yaml_documents()

    completed = 0
    started = time.perf_counter()
    current_phase: str | None = None

    for step in step_tuple:
        if step.phase != current_phase:
            current_phase = step.phase
            banner(f"PHASE: {current_phase}")

        result = run_step(step)
        if not result.success:
            elapsed = time.perf_counter() - started
            print(f"FAILURE: {step.name}: {result.error}")
            return PipelineResult(
                completed=completed,
                failed_step=step.name,
                elapsed_seconds=elapsed,
            )
        completed += 1

    elapsed = time.perf_counter() - started
    banner("PIPELINE COMPLETE")
    print(f"Completed steps: {completed}")
    print(f"Total runtime: {elapsed:.4f}s")
    print("Constitutional closure achieved")

    return PipelineResult(
        completed=completed,
        failed_step=None,
        elapsed_seconds=elapsed,
    )


def _normalize_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def main() -> int:
    result = execute_pipeline()
    return 1 if result.failed_step else 0


if __name__ == "__main__":
    sys.exit(main())
