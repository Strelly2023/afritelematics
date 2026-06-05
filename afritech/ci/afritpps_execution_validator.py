"""Validate the AfriTPPS GA Elite execution pillar."""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path
from types import ModuleType

from afritech.afritpps import (
    constants,
    domain_contracts,
    execution_engine,
    metrics,
    models,
    observability,
    orchestration,
    persistent,
    services,
)
from afritech.afritpps.constants import (
    AFRITPPS_COMPONENT,
    AFRITPPS_COMPONENT_ID,
    AFRITPPS_PILLAR,
    AFRITPPS_STATUS,
    OUTPUTS,
    QUESTION_ANSWERED,
    PURPOSE,
    assert_afritpps_constitution,
    constitutional_afritpps_metadata,
)
from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
    AfriTPPSWorkflowStep,
)
from afritech.afritpps.services import build_operational_model


VALIDATOR_NAME = "afritech.ci.afritpps_execution_validator"

AFRITPPS_ROOT = Path("afritech/afritpps")
AFRITPPS_TEST_ROOT = Path("afritech/tests/afritpps")

REQUIRED_IMPLEMENTATION_FILES = (
    AFRITPPS_ROOT / "__init__.py",
    AFRITPPS_ROOT / "constants.py",
    AFRITPPS_ROOT / "domain_contracts.py",
    AFRITPPS_ROOT / "execution_engine.py",
    AFRITPPS_ROOT / "models.py",
    AFRITPPS_ROOT / "metrics.py",
    AFRITPPS_ROOT / "observability.py",
    AFRITPPS_ROOT / "orchestration.py",
    AFRITPPS_ROOT / "persistent.py",
    AFRITPPS_ROOT / "services.py",
)

REQUIRED_TEST_FILES = (
    AFRITPPS_TEST_ROOT / "__init__.py",
    AFRITPPS_TEST_ROOT / "test_constants.py",
    AFRITPPS_TEST_ROOT / "test_domain_contracts.py",
    AFRITPPS_TEST_ROOT / "test_execution_engine.py",
    AFRITPPS_TEST_ROOT / "test_models.py",
    AFRITPPS_TEST_ROOT / "test_metrics.py",
    AFRITPPS_TEST_ROOT / "test_observability.py",
    AFRITPPS_TEST_ROOT / "test_orchestration.py",
    AFRITPPS_TEST_ROOT / "test_persistent_orchestration.py",
    AFRITPPS_TEST_ROOT / "test_services.py",
    AFRITPPS_TEST_ROOT / "test_validator.py",
)

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
    domain_contracts,
    execution_engine,
    models,
    metrics,
    observability,
    orchestration,
    persistent,
    services,
)


class AfriTPPSValidationError(RuntimeError):
    """Raised when AfriTPPS violates its execution pillar contract."""


def _fail(message: str) -> None:
    raise AfriTPPSValidationError(message)


def _source(module: ModuleType) -> str:
    return inspect.getsource(module)


def _tree(module: ModuleType) -> ast.Module:
    return ast.parse(_source(module))


def validate_required_files() -> None:
    missing = tuple(path for path in REQUIRED_IMPLEMENTATION_FILES if not path.is_file())
    if missing:
        _fail("missing AfriTPPS implementation files: " + ", ".join(map(str, missing)))


def validate_required_tests() -> None:
    missing = tuple(path for path in REQUIRED_TEST_FILES if not path.is_file())
    if missing:
        _fail("missing AfriTPPS test files: " + ", ".join(map(str, missing)))


def validate_identity() -> None:
    if AFRITPPS_COMPONENT != "AfriTPPS":
        _fail("invalid AfriTPPS component")
    if AFRITPPS_COMPONENT_ID != "afritech.afritpps":
        _fail("invalid AfriTPPS component id")
    if AFRITPPS_PILLAR != "EXECUTION":
        _fail("AfriTPPS pillar must be EXECUTION")
    if AFRITPPS_STATUS != "GA_ELITE_EXECUTION_PILLAR":
        _fail("AfriTPPS status must be GA_ELITE_EXECUTION_PILLAR")
    if QUESTION_ANSWERED != "How should it be executed?":
        _fail("AfriTPPS question mismatch")
    if PURPOSE != "Defines how work gets executed.":
        _fail("AfriTPPS purpose mismatch")
    if set(OUTPUTS) != {
        "Capabilities",
        "Workflows",
        "Processes",
        "Programs",
        "Operational Models",
        "Execution Metrics",
    }:
        _fail("AfriTPPS outputs mismatch")


def validate_boundary_flags() -> None:
    assert_afritpps_constitution()
    metadata = constitutional_afritpps_metadata()

    for key in (
        "governance_authority",
        "proof_authority",
        "replay_authority",
        "ci_authority",
        "admissibility_authority",
        "intelligence_authority",
        "engineering_authority",
        "policy_authority",
        "constitutional_authority",
        "mutation_allowed",
        "proof_mutation_allowed",
        "replay_mutation_allowed",
        "governance_mutation_allowed",
        "authority_escalation_allowed",
    ):
        if metadata[key] is not False:
            _fail(f"AfriTPPS boundary flag must be false: {key}")


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
    capability = AfriTPPSCapability(
        capability_id="cap.dispatch",
        name="Dispatch Operations",
        capability_type="service",
        maturity_level="measured",
        owner="operations",
        service_objective="assign rides deterministically",
    )
    workflow = AfriTPPSWorkflow(
        workflow_id="workflow.dispatch",
        name="Dispatch workflow",
        steps=(
            AfriTPPSWorkflowStep(
                step_id="step.1",
                capability_id="cap.dispatch",
                name="Receive request",
                process="intake",
                role="dispatcher",
                expected_output="validated request",
                sequence=1,
                status="ready",
            ),
            AfriTPPSWorkflowStep(
                step_id="step.2",
                capability_id="cap.dispatch",
                name="Assign driver",
                process="assignment",
                role="dispatcher",
                expected_output="driver assignment",
                sequence=2,
                status="planned",
            ),
        ),
    )
    program = AfriTPPSProgram(
        program_id="program.mobility",
        name="Mobility execution program",
        capabilities=(capability,),
        workflows=(workflow,),
    )
    model = build_operational_model(program)

    if model["creates_governance_authority"] is not False:
        _fail("AfriTPPS operational model must not create governance authority")
    if model["creates_proof_authority"] is not False:
        _fail("AfriTPPS operational model must not create proof authority")
    if model["creates_replay_authority"] is not False:
        _fail("AfriTPPS operational model must not create replay authority")
    if model["mutates_proof"] is not False:
        _fail("AfriTPPS operational model must not mutate proof")
    if model["defines_execution"] is not True:
        _fail("AfriTPPS operational model must define execution")


def validate_trust_kernel_binding() -> None:
    source = _source(execution_engine)
    required_text = (
        "process_command",
        "process_client_command",
        "EvidenceBundle",
        "projection_hash",
        "AfriTPPSExecutionOutcome",
        "verified=True",
    )
    for needle in required_text:
        if needle not in source:
            _fail(f"AfriTPPS execution engine missing trust binding: {needle}")


def validate_domain_contracts() -> None:
    expected_domains = {
        "AfriRide",
        "AfriConnect",
        "AfriPay",
        "AfriHealth",
        "AfriLearning",
        "AfriTalent",
        "AfriMarket",
        "AfriHome",
        "AfriID",
        "AfriCloud",
    }
    if set(domain_contracts.DOMAIN_CONTRACTS) != expected_domains:
        _fail("AfriTPPS domain contract registry mismatch")
    if domain_contracts.DOMAIN_CONTRACTS["AfriPay"].execution_allowed is not False:
        _fail("AfriPay domain contract must remain execution-blocked")

    source = _source(domain_contracts)
    required_text = (
        "execute_operation",
        "execute_domain_operation",
        "AfriTPPSContractError",
        "execution_allowed=False",
        "DESIGNED_BLOCKED",
    )
    for needle in required_text:
        if needle not in source:
            _fail(f"AfriTPPS domain contracts missing enforcement text: {needle}")


def validate_orchestration_binding() -> None:
    source = _source(orchestration)
    required_text = (
        "execute_domain_operation",
        "dependencies",
        "outcome.verified",
        "projection_hash",
        "fully_verified=True",
    )
    for needle in required_text:
        if needle not in source:
            _fail(f"AfriTPPS orchestration missing enforcement text: {needle}")


def validate_observability_and_control() -> None:
    observability_source = _source(observability)
    persistent_source = _source(persistent)
    for needle in (
        "OrchestrationView",
        "StepView",
        "DependencyEdge",
        "build_orchestration_view",
    ):
        if needle not in observability_source:
            _fail(f"AfriTPPS observability missing graph view text: {needle}")
    for needle in (
        "pause_orchestration",
        "resume_orchestration",
        "abort_orchestration",
        "OperatorActionLog",
        "PersistentOrchestration",
        "OrchestrationStepState",
    ):
        if needle not in persistent_source:
            _fail(f"AfriTPPS persistent control missing text: {needle}")


def validate_afritpps_execution_surface() -> None:
    validate_required_files()
    validate_required_tests()
    validate_identity()
    validate_boundary_flags()
    validate_forbidden_imports_and_calls()
    validate_behavior()
    validate_trust_kernel_binding()
    validate_domain_contracts()
    validate_orchestration_binding()
    validate_observability_and_control()


def main() -> int:
    try:
        validate_afritpps_execution_surface()
        print("AfriTPPS execution validation PASSED")
        return 0
    except Exception as exc:
        print(f"AfriTPPS execution validation FAILED: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
