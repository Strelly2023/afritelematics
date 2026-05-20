from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/qa/AfriRide_Test_Plan_Document.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL VALIDATION SURFACE",
    "CLASSIFICATION: ISOLATED OPERATIONAL VALIDATION SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay admissibility",
    "core invariants",
    "execution legality",
    "identity ontology",
)

TEST_LEVELS = (
    "Unit Testing",
    "Integration Testing",
    "API Testing",
    "Replay Validation Testing",
    "Continuity Testing",
    "Governance Testing",
    "Documentation Boundary Testing",
    "Adversarial Testing",
)

CI_COMMANDS = (
    "python3 -m afritech.ci.constitutional_validation",
    "python3 -m afritech.verify.replay",
    "python3 -m afritech.demo.proof",
    "pytest -q",
)

QUALITY_GATES = (
    "constitutional validation",
    "replay validation",
    "proof validation",
    "pytest suite",
    "claim-discipline validation",
    "implementation admissibility validation",
)

DEFECT_CLASSES = (
    "Critical",
    "Major",
    "Minor",
)

FORBIDDEN_INFLATION = (
    "global deployment readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale marketplace guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_test_plan_has_operational_validation_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not redefine" in text
    for surface in NON_REDEFINED_SURFACES:
        assert surface in text


def test_test_plan_declares_objectives_scope_and_strategy() -> None:
    text = read_doc()
    lowered = text.lower()

    for objective in (
        "ride lifecycle correctness",
        "deterministic execution",
        "replay equivalence",
        "continuity preservation",
        "identity integrity",
        "claim-evidence validity",
        "closed-world enforcement",
    ):
        assert objective in lowered

    assert "included scope" in lowered
    assert "excluded scope" in lowered
    assert "layered validation" in lowered
    assert "global production readiness" in lowered
    assert "universal state-space exhaustiveness" in lowered


def test_test_plan_defines_test_levels_and_examples() -> None:
    text = read_doc()

    for level in TEST_LEVELS:
        assert level in text

    for component in (
        "RideRequestValidator",
        "RideRequestService",
        "MatchingService",
        "RideLifecycleService",
        "PricingService",
        "NotificationService",
        "PaymentService",
    ):
        assert component in text

    assert "def test_missing_origin()" in text
    assert "def test_invalid_transition()" in text
    assert "def test_full_ride_flow()" in text


def test_test_plan_defines_api_replay_continuity_and_adversarial_testing() -> None:
    text = read_doc()

    for endpoint in (
        "POST /api/v1/rides",
        "GET /api/v1/rides/{ride_id}",
        "POST /api/v1/rides/{ride_id}/transition",
    ):
        assert endpoint in text

    for target in (
        "trace reconstruction",
        "deterministic convergence",
        "driver dropout",
        "timeout recovery",
        "duplicate authority prevention",
        "reflection injection",
        "illegal alias injection",
        "replay tampering",
        "topology mutation",
    ):
        assert target in text


def test_test_plan_defines_ci_commands_quality_gates_and_defects() -> None:
    text = read_doc()

    for command in CI_COMMANDS:
        assert command in text

    for gate in QUALITY_GATES:
        assert gate in text

    for defect_class in DEFECT_CLASSES:
        assert defect_class in text

    assert "FAIL_FAST" in text
    assert "replay divergence" in text
    assert "identity corruption" in text
    assert "notification delivery issues" in text


def test_test_plan_preserves_acceptance_environment_and_constraints() -> None:
    text = read_doc()

    for acceptance in (
        "all lifecycle tests pass",
        "replay equivalence passes",
        "continuity scenarios pass",
        "constitutional validation passes",
        "claim-evidence-implementation binding passes",
    ):
        assert acceptance in text

    for environment in ("Python 3.11", "pytest", "Django", "GitHub Actions CI"):
        assert environment in text

    for surface in ("afritech/", "afriride_system/", "tests/", "docs/"):
        assert surface in text

    for forbidden in (
        "mutate proof truth",
        "bypass replay validation",
        "permit undeclared execution",
        "treat documentation as authority",
    ):
        assert forbidden in text


def test_test_plan_bounds_risk_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "bounded deterministic correctness" in lowered
    assert "bounded deterministic testing surface" in lowered
    assert "under afritech constitutional admissibility enforcement" in lowered

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered

    assert "global deployment readiness" in lowered
    assert "universal fault tolerance" in lowered
    assert "complete state-space exhaustiveness" in lowered
    assert "infinite-scale marketplace guarantees" in lowered
