"""Validate the AfriProgramming GA Elite engineering pillar."""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from types import ModuleType

from afritech.afriprogramming import constants, models, services
from afritech.afriprogramming.constants import (
    AFRIPROGRAMMING_COMPONENT,
    AFRIPROGRAMMING_COMPONENT_ID,
    AFRIPROGRAMMING_PILLAR,
    AFRIPROGRAMMING_STATUS,
    CANONICAL_DEFINITION,
    FEATURE_GROUPS,
    OUTPUTS,
    QUESTION_ANSWERED,
    PURPOSE,
    assert_afriprogramming_constitution,
    constitutional_afriprogramming_metadata,
)
from afritech.afriprogramming.models import (
    AfriProgrammingAgent,
    AfriProgrammingArtifact,
    AfriProgrammingEngineeringPlan,
    AfriProgrammingTask,
)
from afritech.afriprogramming.services import build_engineering_platform


VALIDATOR_NAME = "afritech.ci.afriprogramming_engineering_validator"

AFRIPROGRAMMING_ROOT = Path("afritech/afriprogramming")
AFRIPROGRAMMING_TEST_ROOT = Path("afritech/tests/afriprogramming")

REQUIRED_IMPLEMENTATION_FILES = (
    AFRIPROGRAMMING_ROOT / "__init__.py",
    AFRIPROGRAMMING_ROOT / "constants.py",
    AFRIPROGRAMMING_ROOT / "models.py",
    AFRIPROGRAMMING_ROOT / "services.py",
)

REQUIRED_TEST_FILES = (
    AFRIPROGRAMMING_TEST_ROOT / "__init__.py",
    AFRIPROGRAMMING_TEST_ROOT / "test_constants.py",
    AFRIPROGRAMMING_TEST_ROOT / "test_models.py",
    AFRIPROGRAMMING_TEST_ROOT / "test_services.py",
    AFRIPROGRAMMING_TEST_ROOT / "test_validator.py",
)

REQUIRED_FEATURE_GROUPS = {
    "Autonomous Engineering Agent",
    "Multi-Agent Engineering",
    "Codebase Intelligence",
    "Autonomous Software Development Lifecycle",
    "Proof-Aware Engineering",
    "Constitutional Engineering",
    "Software Verification",
    "Testing Platform",
    "Sandbox Execution",
    "Pull Request Intelligence",
    "Developer Workspace",
    "Agent Skills Marketplace",
    "Security Engineering",
    "Explainable Engineering",
    "Knowledge Graph Engineering",
    "Enterprise Portfolio Management",
    "AfriTech Ecosystem Integration",
}

FORBIDDEN_IMPORT_PREFIXES = (
    "afritech.governance",
    "afritech.proof.constitutional_receipt",
    "afritech.ci.constitutional_validation",
)

FORBIDDEN_CALL_NAMES = (
    "open",
    "save",
    "delete",
    "execute_from_command_line",
    "safe_load",
    "load",
)

VALIDATED_MODULES: tuple[ModuleType, ...] = (
    constants,
    models,
    services,
)


class AfriProgrammingValidationError(RuntimeError):
    """Raised when AfriProgramming violates its engineering pillar contract."""


def _fail(message: str) -> None:
    raise AfriProgrammingValidationError(message)


def _source(module: ModuleType) -> str:
    return inspect.getsource(module)


def _tree(module: ModuleType) -> ast.Module:
    return ast.parse(_source(module))


def validate_required_files() -> None:
    missing = tuple(path for path in REQUIRED_IMPLEMENTATION_FILES if not path.is_file())
    if missing:
        _fail(
            "missing AfriProgramming implementation files: "
            + ", ".join(map(str, missing))
        )


def validate_required_tests() -> None:
    missing = tuple(path for path in REQUIRED_TEST_FILES if not path.is_file())
    if missing:
        _fail("missing AfriProgramming test files: " + ", ".join(map(str, missing)))


def validate_identity() -> None:
    if AFRIPROGRAMMING_COMPONENT != "AfriProgramming":
        _fail("invalid AfriProgramming component")
    if AFRIPROGRAMMING_COMPONENT_ID != "afritech.afriprogramming":
        _fail("invalid AfriProgramming component id")
    if AFRIPROGRAMMING_PILLAR != "ENGINEERING":
        _fail("AfriProgramming pillar must be ENGINEERING")
    if AFRIPROGRAMMING_STATUS != "GA_ELITE_AUTONOMOUS_ENGINEERING_PLATFORM":
        _fail("AfriProgramming status mismatch")
    if QUESTION_ANSWERED != "How do we build it?":
        _fail("AfriProgramming question mismatch")
    if PURPOSE != "Builds and verifies software systems.":
        _fail("AfriProgramming purpose mismatch")
    if CANONICAL_DEFINITION != (
        "AfriProgramming is a proof-aware autonomous engineering platform that "
        "combines AI software agents, software lifecycle automation, verification, "
        "testing, constitutional governance, and engineering intelligence to build, "
        "validate, and evolve intelligent software systems."
    ):
        _fail("AfriProgramming canonical definition mismatch")
    if set(OUTPUTS) != {
        "Code",
        "Tests",
        "Validators",
        "Runtime Systems",
        "Proof Artifacts",
        "Software Platforms",
    }:
        _fail("AfriProgramming outputs mismatch")


def validate_feature_groups() -> None:
    if set(FEATURE_GROUPS) != REQUIRED_FEATURE_GROUPS:
        _fail("AfriProgramming GA Elite feature groups mismatch")


def validate_boundary_flags() -> None:
    assert_afriprogramming_constitution()
    metadata = constitutional_afriprogramming_metadata()

    for key in (
        "governance_authority",
        "proof_authority",
        "replay_authority",
        "ci_authority",
        "admissibility_authority",
        "intelligence_authority",
        "execution_authority",
        "policy_authority",
        "constitutional_authority",
        "mutation_allowed",
        "proof_mutation_allowed",
        "replay_mutation_allowed",
        "governance_mutation_allowed",
        "authority_escalation_allowed",
    ):
        if metadata[key] is not False:
            _fail(f"AfriProgramming boundary flag must be false: {key}")


def validate_forbidden_imports_and_calls() -> None:
    for module in VALIDATED_MODULES:
        tree = _tree(module)
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        _fail(f"{module.__name__} has forbidden import {alias.name}")

            if isinstance(item, ast.ImportFrom):
                module_name = item.module or ""
                if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{module.__name__} has forbidden import {module_name}")

            if isinstance(item, ast.Call):
                call_name = ""
                if isinstance(item.func, ast.Name):
                    call_name = item.func.id
                elif isinstance(item.func, ast.Attribute):
                    call_name = item.func.attr
                if call_name in FORBIDDEN_CALL_NAMES:
                    _fail(f"{module.__name__} has forbidden call {call_name}")


def validate_behavior() -> None:
    task = AfriProgrammingTask(
        task_id="task.engineering.ga",
        intent="Build proof-aware autonomous engineering workflow",
        lifecycle_stage="build",
        required_capabilities=(
            "code_generation",
            "test_generation",
            "security_validation",
            "pr_explanation",
            "verification_receipts",
        ),
        evidence_refs=("claim.ga.engineering",),
    )
    agents = (
        AfriProgrammingAgent(
            agent_id="agent.backend",
            name="Backend Agent",
            role="backend",
            capabilities=("code_generation", "pr_explanation"),
        ),
        AfriProgrammingAgent(
            agent_id="agent.test",
            name="Testing Agent",
            role="testing",
            capabilities=("test_generation", "verification_receipts"),
        ),
        AfriProgrammingAgent(
            agent_id="agent.security",
            name="Security Agent",
            role="security",
            capabilities=("security_validation",),
        ),
    )
    artifacts = (
        AfriProgrammingArtifact(
            artifact_id="artifact.code",
            artifact_type="CODE",
            title="Engineering implementation",
            source_task_id="task.engineering.ga",
            trace_refs=("claim.ga.engineering",),
        ),
        AfriProgrammingArtifact(
            artifact_id="artifact.receipt",
            artifact_type="VERIFICATION_RECEIPT",
            title="Verification receipt",
            source_task_id="task.engineering.ga",
            trace_refs=("claim.ga.engineering",),
        ),
        AfriProgrammingArtifact(
            artifact_id="artifact.pr",
            artifact_type="PR_EXPLANATION",
            title="Pull request explanation",
            source_task_id="task.engineering.ga",
            trace_refs=("claim.ga.engineering",),
        ),
    )
    plan = AfriProgrammingEngineeringPlan(
        plan_id="plan.ga.engineering",
        task=task,
        agents=agents,
        artifacts=artifacts,
    )
    platform = build_engineering_platform(plan)

    if platform["engineers_systems"] is not True:
        _fail("AfriProgramming platform must engineer systems")
    if platform["proof_aware"] is not True:
        _fail("AfriProgramming platform must be proof-aware")
    if platform["creates_governance_authority"] is not False:
        _fail("AfriProgramming must not create governance authority")
    if platform["creates_proof_authority"] is not False:
        _fail("AfriProgramming must not create proof authority")
    if platform["creates_replay_authority"] is not False:
        _fail("AfriProgramming must not create replay authority")
    if platform["mutates_proof"] is not False:
        _fail("AfriProgramming must not mutate proof")
    if platform["pull_request_intelligence"]["merge_recommendation_ready"] is not True:
        _fail("AfriProgramming PR intelligence must be merge-recommendation ready")


def validate_afriprogramming_engineering_surface() -> None:
    validate_required_files()
    validate_required_tests()
    validate_identity()
    validate_feature_groups()
    validate_boundary_flags()
    validate_forbidden_imports_and_calls()
    validate_behavior()


def main() -> int:
    try:
        validate_afriprogramming_engineering_surface()
        print("AfriProgramming engineering validation PASSED")
        return 0
    except Exception as exc:
        print(f"AfriProgramming engineering validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
