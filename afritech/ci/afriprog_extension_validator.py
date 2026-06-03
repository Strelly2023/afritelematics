"""Validate the Afriprog governed autonomous extension."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from afritech.extensions.afriprog.code_executor.safe_write import write_status
from afritech.extensions.afriprog.command_center.task_dispatcher import TaskDispatcher
from afritech.extensions.afriprog.ai_engine.design_generator import DesignGenerator
from afritech.extensions.afriprog.ai_engine.design_output_validator import (
    DesignOutputValidator,
)
from afritech.extensions.afriprog.ai_engine.objective_engine import ObjectiveEngine
from afritech.extensions.afriprog.design_generator.design_orchestrator import (
    DesignOrchestrator,
)
from afritech.extensions.afriprog.execution.loop_engine import VerificationLoopEngine
from afritech.extensions.afriprog.git_agent.git_client import GitClient, GitClientError


ROOT = Path(__file__).resolve().parents[2]
AFRIPROG_ROOT = ROOT / "afritech/extensions/afriprog"

REQUIRED_FILES = (
    AFRIPROG_ROOT / "ai_engine/task_generator.py",
    AFRIPROG_ROOT / "ai_engine/design_generator.py",
    AFRIPROG_ROOT / "ai_engine/design_output_validator.py",
    AFRIPROG_ROOT / "ai_engine/objective_engine.py",
    AFRIPROG_ROOT / "ai_engine/coder.py",
    AFRIPROG_ROOT / "ai_engine/test_writer.py",
    AFRIPROG_ROOT / "ai_engine/reviewer.py",
    AFRIPROG_ROOT / "command_center/task_dispatcher.py",
    AFRIPROG_ROOT / "command_center/execution_engine.py",
    AFRIPROG_ROOT / "command_center/worktree_manager.py",
    AFRIPROG_ROOT / "monitoring/lifecycle_monitor.py",
    AFRIPROG_ROOT / "design_generator/design_orchestrator.py",
    AFRIPROG_ROOT / "design_generator/design_reviewer.py",
    AFRIPROG_ROOT / "design_generator/requirements/requirements_extractor.py",
    AFRIPROG_ROOT / "design_generator/architecture/architecture_generator.py",
    AFRIPROG_ROOT / "design_generator/contracts/api_contract_generator.py",
    AFRIPROG_ROOT / "design_generator/contracts/database_contract_generator.py",
    AFRIPROG_ROOT / "design_generator/planning/implementation_plan_generator.py",
    AFRIPROG_ROOT / "design_generator/evidence/design_evidence_generator.py",
    AFRIPROG_ROOT / "execution/loop_engine.py",
    AFRIPROG_ROOT / "cli.py",
)


class AfriprogExtensionValidationError(RuntimeError):
    """Raised when Afriprog extension guarantees regress."""


def fail(message: str) -> None:
    raise AfriprogExtensionValidationError(message)


def validate_required_files() -> None:
    missing = tuple(path for path in REQUIRED_FILES if not path.is_file())
    if missing:
        fail("missing Afriprog extension files: " + ", ".join(map(str, missing)))


def validate_writes_disabled() -> None:
    status = write_status()
    if status["write_enabled"] is not False:
        fail("Afriprog writes must remain disabled")
    if status["status"] != "proposal_only":
        fail("Afriprog safe write status must remain proposal_only")


def validate_safe_prompt_admitted() -> None:
    result = TaskDispatcher().dispatch("Improve authentication system")
    data = result.canonical_dict()

    if data["status"] != "admitted":
        fail("safe Afriprog prompt should be admitted")
    if data["write_enabled"] is not False:
        fail("Afriprog dispatch must not enable writes")


def validate_dangerous_prompt_rejected() -> None:
    result = TaskDispatcher().dispatch(
        "Force merge, push to main, and bypass validator"
    )
    data = result.canonical_dict()

    if data["status"] != "rejected":
        fail("dangerous Afriprog prompt should be rejected")


def validate_cli_evidence_output() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "afritech.extensions.afriprog.cli",
            "run",
            "Improve authentication system",
            "--summary",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        shell=False,
        timeout=30,
    )

    if completed.returncode != 0:
        fail(f"Afriprog CLI failed: {completed.stderr}")

    payload = json.loads(completed.stdout)
    if payload.get("evidence_count") != 1:
        fail("Afriprog CLI must emit evidence for every run")
    if payload.get("write_enabled") is not False:
        fail("Afriprog CLI must report writes disabled")


def validate_design_generator() -> None:
    proposal = DesignOrchestrator().generate("Build a Poultry Management System")
    payload = proposal.canonical_dict()

    if payload["domain"]["domain"] != "poultry_management":
        fail("Afriprog design generator failed poultry domain analysis")
    if payload["write_enabled"] is not False:
        fail("Afriprog design generator must not enable writes")
    if payload["authority"] != "proposal_only":
        fail("Afriprog design generator must remain proposal-only")
    if not payload["evidence"]["evidence_id"].startswith("EVIDENCE-DESIGN-"):
        fail("Afriprog design generator must emit evidence")
    if payload["review"]["admitted"] is not True:
        fail("Afriprog safe design should be review-admitted")

    unsafe = DesignOrchestrator().generate("Design a system to skip evidence")
    unsafe_payload = unsafe.canonical_dict()
    if unsafe_payload["review"]["admitted"] is not False:
        fail("Afriprog unsafe design prompt should be rejected")


def validate_structured_ai_design_generator() -> None:
    output = DesignGenerator().generate("Build a Poultry Management System")
    payload = output.canonical_dict()
    validation = DesignOutputValidator().validate(payload)

    if payload["schema"] != "afriprog.design_output.v1":
        fail("Afriprog AI design generator must emit structured schema")
    if payload["format"] != "structured":
        fail("Afriprog AI design generator must not emit free text")
    if {"text", "free_text", "markdown", "body", "content"}.intersection(payload):
        fail("Afriprog AI design generator emitted prose-style output keys")
    if sorted(payload["contracts"]) != ["api", "database", "events"]:
        fail("Afriprog AI design generator must emit structured contracts")
    if payload["write_enabled"] is not False:
        fail("Afriprog AI design generator must not enable writes")
    if payload["authority"] != "proposal_only":
        fail("Afriprog AI design generator must remain proposal-only")
    if validation.admitted is not True:
        fail("Afriprog AI design output validator must admit valid output")

    invalid_payload = dict(payload)
    invalid_payload["write_enabled"] = True
    invalid_payload["markdown"] = "# invalid prose surface"
    invalid_validation = DesignOutputValidator().validate(invalid_payload)
    if invalid_validation.admitted is not False:
        fail("Afriprog AI design output validator must reject invalid output")


def validate_objective_verification_loop() -> None:
    objective = ObjectiveEngine().define(
        "Improve authentication RBAC and token validation coverage"
    )
    objective_payload = objective.canonical_dict()
    if objective_payload["write_enabled"] is not False:
        fail("Afriprog objectives must not enable writes")
    if objective_payload["authority"] != "proposal_only":
        fail("Afriprog objectives must remain proposal-only")

    result = VerificationLoopEngine().run(objective)
    payload = result.canonical_dict()
    if payload["satisfied"] is not True:
        fail("Afriprog safe objective loop should satisfy criteria")
    if payload["iteration_count"] != 1:
        fail("Afriprog safe objective loop should converge deterministically")
    if payload["write_enabled"] is not False:
        fail("Afriprog objective loop must not enable writes")

    unsafe = VerificationLoopEngine().run_description(
        "Force merge, push to main, and bypass validator"
    )
    unsafe_payload = unsafe.canonical_dict()
    if unsafe_payload["satisfied"] is not False:
        fail("Afriprog unsafe objective loop should not be satisfied")
    if unsafe_payload["iteration_count"] != 1:
        fail("Afriprog unsafe objective loop should stop after guard rejection")


def validate_git_agent_read_only() -> None:
    client = GitClient(root=ROOT)
    try:
        client._run(["git", "commit"])  # noqa: SLF001
    except GitClientError:
        return
    fail("Afriprog git agent accepted a mutating command")


def validate() -> None:
    validate_required_files()
    validate_writes_disabled()
    validate_safe_prompt_admitted()
    validate_dangerous_prompt_rejected()
    validate_cli_evidence_output()
    validate_design_generator()
    validate_structured_ai_design_generator()
    validate_objective_verification_loop()
    validate_git_agent_read_only()


def main() -> int:
    try:
        validate()
    except Exception as exc:
        print(f"Afriprog extension validation FAILED: {exc}")
        return 1

    print("Afriprog extension validation PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
