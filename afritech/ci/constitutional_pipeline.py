# afritech/ci/constitutional_pipeline.py

"""
AfriTech Constitutional Pipeline
================================

Deterministic constitutional orchestration pipeline.

Scope:
- invariant compilation
- semantic validation
- completeness generation
- static enforcement validation

Guarantees:
- deterministic execution ordering
- fail-closed orchestration
- closed-world execution
- strict invariant alignment
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import yaml

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

# ============================================================
# ROOT
# ============================================================

ROOT = Path.cwd()


# ============================================================
# ENV HARDENING (DETERMINISM)
# ============================================================

os.environ["PYTHONHASHSEED"] = "0"


# ============================================================
# ERRORS
# ============================================================

class ConstitutionalPipelineError(Exception):
    pass


# ============================================================
# STEP
# ============================================================

@dataclass(frozen=True)
class PipelineStep:
    name: str
    command: list[str]
    phase: str


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class PipelineResult:
    completed: int
    failed_step: str | None
    elapsed_seconds: float
    deterministic: bool = True


# ============================================================
# UTILITIES
# ============================================================

def banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ============================================================
# EXECUTION
# ============================================================

def run_step(step: PipelineStep) -> None:

    print(f"\n🔍 Running {step.name}...")

    start = time.perf_counter()

    try:
        result = subprocess.run(
            step.command,
            cwd=ROOT,
            text=True,
            shell=False,
            capture_output=True,
        )

    except Exception as exc:
        raise ConstitutionalPipelineError(
            f"{step.name} execution error: {exc}"
        )

    elapsed = time.perf_counter() - start

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    if result.returncode != 0:
        raise ConstitutionalPipelineError(
            f"{step.name} failed\n"
            f"phase: {step.phase}\n"
            f"exit_code: {result.returncode}\n"
            f"elapsed: {elapsed:.4f}s\n"
            f"stderr:\n{result.stderr.strip()}"
        )

    print(f"✅ {step.name} passed ({elapsed:.4f}s)")


# ============================================================
# YAML VALIDATION
# ============================================================

def validate_yaml_documents() -> None:

    banner("PHASE 0: YAML VALIDATION")

    targets = [
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
        "afritech/runtime/policies/replay_compression.yaml",
        "afritech/runtime/contracts/witness_recovery_contract.yaml",
    ]

    for path in targets:

        p = Path(path)

        if not p.exists():
            raise ConstitutionalPipelineError(f"Missing file: {path}")

        try:
            yaml.safe_load(p.read_text(encoding="utf-8"))
            print(f"✅ {path}")

        except Exception as e:
            raise ConstitutionalPipelineError(
                f"Invalid YAML {path}: {e}"
            )


# ============================================================
# PIPELINE (NO TESTS)
# ============================================================

PIPELINE: tuple[PipelineStep, ...] = (

    # --------------------------------------------------------
    # CONSTITUTION
    # --------------------------------------------------------

    PipelineStep(
        name="compile_invariants",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.constitution.compiler.compile_invariants",
            "--execution",
            "afritech/constitution/INVARIANTS.yaml",
            "--semantics",
            "afritech/constitution/invariants_semantics.yaml",
            "--out",
            "afritech/constitution/compiled/invariants_ir.json",
        ],
    ),

    PipelineStep(
        name="verify_semantic_coverage",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.constitution.verify_semantic_coverage",
        ],
    ),

    PipelineStep(
        name="semantic_kernel_validator",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.ci.semantic_kernel_validator",
        ],
    ),

    PipelineStep(
        name="adversarial_runner_validator",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.ci.adversarial_runner_validator",
        ],
    ),

    PipelineStep(
        name="semantic_directionality_validator",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.ci.semantic_directionality_validator",
        ],
    ),

    PipelineStep(
        name="governance_size_validator",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.ci.governance_size_validator",
        ],
    ),

    PipelineStep(
        name="receipt_validator",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.ci.receipt_validator",
        ],
    ),

    PipelineStep(
        name="generate_completeness",
        phase="CONSTITUTION",
        command=[
            sys.executable,
            "-m",
            "afritech.proof.generate_completeness",
        ],
    ),

    # --------------------------------------------------------
    # STATIC VALIDATION
    # --------------------------------------------------------

    PipelineStep(
        name="ast_import_validator",
        phase="STATIC",
        command=[
            sys.executable,
            "-m",
            "afritech.ci.ast_import_validator",
        ],
    ),

    PipelineStep(
        name="compileall_afritech",
        phase="STATIC",
        command=[
            sys.executable,
            "-m",
            "compileall",
            "afritech",
        ],
    ),
)


# ============================================================
# EXECUTION ENGINE
# ============================================================

def execute_pipeline(
    steps: Iterable[PipelineStep] = PIPELINE,
) -> PipelineResult:

    validate_yaml_documents()

    current_phase = None
    completed = 0
    started = time.perf_counter()

    try:

        for step in steps:

            if step.phase != current_phase:
                current_phase = step.phase
                banner(f"PHASE: {current_phase}")

            run_step(step)
            completed += 1

    except ConstitutionalPipelineError as e:

        elapsed = time.perf_counter() - started

        print(f"\n❌ FAILURE: {e}")

        return PipelineResult(
            completed=completed,
            failed_step=step.name,
            elapsed_seconds=elapsed,
        )

    elapsed = time.perf_counter() - started

    banner("PIPELINE COMPLETE")

    print(f"✅ Completed steps: {completed}")
    print(f"✅ Total runtime: {elapsed:.4f}s")
    print("✅ Constitutional closure achieved")

    return PipelineResult(
        completed=completed,
        failed_step=None,
        elapsed_seconds=elapsed,
    )


# ============================================================
# ENTRYPOINT
# ============================================================

if __name__ == "__main__":

    result = execute_pipeline()

    if result.failed_step:
        sys.exit(1)
