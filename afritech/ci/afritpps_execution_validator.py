"""Validate the AfriTPPS GA Elite execution pillar."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


VALIDATOR_NAME = "afritech.ci.afritpps_execution_validator"

AFRITPPS_ROOT = Path("afritech/afritpps")
AFRITPPS_TEST_ROOT = Path("afritech/tests/afritpps")
CONSTANTS_FILE = AFRITPPS_ROOT / "constants.py"
MODELS_FILE = AFRITPPS_ROOT / "models.py"
SERVICES_FILE = AFRITPPS_ROOT / "services.py"
EXECUTION_ENGINE_FILE = AFRITPPS_ROOT / "execution_engine.py"
DOMAIN_CONTRACTS_FILE = AFRITPPS_ROOT / "domain_contracts.py"
ORCHESTRATION_FILE = AFRITPPS_ROOT / "orchestration.py"
OBSERVABILITY_FILE = AFRITPPS_ROOT / "observability.py"
PERSISTENT_FILE = AFRITPPS_ROOT / "persistent.py"
METRICS_FILE = AFRITPPS_ROOT / "metrics.py"

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

VALIDATED_SOURCE_FILES = (
    CONSTANTS_FILE,
    DOMAIN_CONTRACTS_FILE,
    EXECUTION_ENGINE_FILE,
    MODELS_FILE,
    METRICS_FILE,
    OBSERVABILITY_FILE,
    ORCHESTRATION_FILE,
    PERSISTENT_FILE,
    SERVICES_FILE,
)

_CONSTANTS = {}


class AfriTPPSValidationError(RuntimeError):
    """Raised when AfriTPPS violates its execution pillar contract."""


def _fail(message: str) -> None:
    raise AfriTPPSValidationError(message)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path), filename=str(path))


def _literal_assignments(path: Path) -> dict[str, object]:
    assignments: dict[str, object] = {}
    for node in _tree(path).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            assignments[target.id] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
    return assignments


def _constant(name: str) -> object:
    global _CONSTANTS
    if not _CONSTANTS:
        _CONSTANTS = _literal_assignments(CONSTANTS_FILE)
    return globals().get(name, _CONSTANTS.get(name))


AFRITPPS_COMPONENT = "AfriTPPS"
AFRITPPS_COMPONENT_ID = "afritech.afritpps"
AFRITPPS_PILLAR = "EXECUTION"
AFRITPPS_STATUS = "GA_ELITE_EXECUTION_PILLAR"
QUESTION_ANSWERED = "How should it be executed?"
PURPOSE = "Defines how work gets executed."
OUTPUTS = (
    "Capabilities",
    "Workflows",
    "Processes",
    "Programs",
    "Operational Models",
    "Execution Metrics",
)


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
    false_flags = (
        "GOVERNANCE_AUTHORITY",
        "PROOF_AUTHORITY",
        "REPLAY_AUTHORITY",
        "CI_AUTHORITY",
        "ADMISSIBILITY_AUTHORITY",
        "INTELLIGENCE_AUTHORITY",
        "ENGINEERING_AUTHORITY",
        "POLICY_AUTHORITY",
        "CONSTITUTIONAL_AUTHORITY",
        "MUTATION_ALLOWED",
        "PROOF_MUTATION_ALLOWED",
        "REPLAY_MUTATION_ALLOWED",
        "GOVERNANCE_MUTATION_ALLOWED",
        "AUTHORITY_ESCALATION_ALLOWED",
    )
    true_flags = (
        "EXECUTION_PILLAR",
        "OPERATIONAL_CAPABILITY",
        "WORKFLOW_ORCHESTRATION",
        "PROCESS_EXECUTION",
        "PROGRAM_EXECUTION",
        "PERFORMANCE_MANAGEMENT",
        "CAPABILITY_MATURITY",
    )

    for flag in false_flags:
        if _constant(flag) is not False:
            _fail(f"AfriTPPS boundary flag must be false: {flag}")
    for flag in true_flags:
        if _constant(flag) is not True:
            _fail(f"AfriTPPS execution flag must be true: {flag}")

    constants_source = _source(CONSTANTS_FILE)
    for needle in (
        "constitutional_afritpps_metadata",
        "assert_afritpps_constitution",
        "forbidden_authority_flags",
        "required_execution_flags",
    ):
        if needle not in constants_source:
            _fail(f"AfriTPPS constants missing boundary guard text: {needle}")


def validate_forbidden_imports_and_calls() -> None:
    for path in VALIDATED_SOURCE_FILES:
        tree = _tree(path)
        for item in ast.walk(tree):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    if alias.name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                        _fail(f"{path} has forbidden import {alias.name}")

            if isinstance(item, ast.ImportFrom):
                module_name = item.module or ""
                if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    _fail(f"{path} has forbidden import {module_name}")

            if isinstance(item, ast.Call):
                call_name = ""
                if isinstance(item.func, ast.Name):
                    call_name = item.func.id
                elif isinstance(item.func, ast.Attribute):
                    call_name = item.func.attr
                if call_name in FORBIDDEN_CALL_NAMES:
                    _fail(f"{path} has forbidden call {call_name}")


def validate_behavior() -> None:
    models_source = _source(MODELS_FILE)
    services_source = _source(SERVICES_FILE)
    for needle in (
        "AfriTPPSCapability",
        "AfriTPPSWorkflowStep",
        "AfriTPPSWorkflow",
        "AfriTPPSProgram",
        "canonical_dict",
        '"creates_governance_authority": False',
        '"creates_proof_authority": False',
        '"creates_replay_authority": False',
        '"mutates_proof": False',
    ):
        if needle not in models_source:
            _fail(f"AfriTPPS models missing behavior text: {needle}")

    for needle in (
        "build_operational_model",
        '"defines_execution": True',
        '"creates_governance_authority": False',
        '"creates_proof_authority": False',
        '"creates_replay_authority": False',
        '"mutates_proof": False',
    ):
        if needle not in services_source:
            _fail(f"AfriTPPS services missing behavior text: {needle}")


def validate_trust_kernel_binding() -> None:
    source = _source(EXECUTION_ENGINE_FILE)
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
    source = _source(DOMAIN_CONTRACTS_FILE)
    for domain in expected_domains:
        if f'"{domain}"' not in source:
            _fail(f"AfriTPPS domain contract registry missing {domain}")
    if '"AfriPay"' not in source or "execution_allowed=False" not in source:
        _fail("AfriPay domain contract must remain execution-blocked")

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
    source = _source(ORCHESTRATION_FILE)
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
    observability_source = _source(OBSERVABILITY_FILE)
    persistent_source = _source(PERSISTENT_FILE)
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
