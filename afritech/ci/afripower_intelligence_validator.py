"""
CI validator for AFRIPower enterprise intelligence projection.

This validator enforces the AFRIPower boundary:

- AFRIPower may observe.
- AFRIPower may explain.
- AFRIPower may project.
- AFRIPower may support enterprise intelligence views.

AFRIPower must not:
- execute runtime behavior
- validate runtime truth
- enforce governance
- mutate receipts
- mutate proof artifacts
- create replay authority
- create proof authority
- create CI authority
- create governance authority
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable, Sequence

from afritech.afripower.constants import (
    AFRIPOWER_COMPONENT,
    AFRIPOWER_COMPONENT_ID,
    AFRIPOWER_PROJECTION_STATUS,
    AUTHORITATIVE,
    CI_AUTHORITY,
    DECISION_AUTHORITY,
    ENFORCEMENT_AUTHORITY,
    ENTERPRISE_INTELLIGENCE_ONLY,
    GOVERNANCE_AUTHORITY,
    GOVERNANCE_MUTATION_ALLOWED,
    INTELLIGENCE_AUTHORITY,
    INTELLIGENCE_STATUS,
    LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_CI,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
    LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
    LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    LAW_AFRIPOWER_IS_DISPLAY_ONLY,
    LAW_AFRIPOWER_IS_NON_AUTHORITATIVE,
    LAW_AFRIPOWER_IS_READ_ONLY,
    MUTATION_ALLOWED,
    OBSERVATIONAL_ONLY,
    PROJECTION_CREATES_AUTHORITY,
    PROJECTION_ONLY,
    PROOF_AUTHORITY,
    PROOF_MUTATION_ALLOWED,
    READ_ONLY,
    RECEIPT_MUTATION_ALLOWED,
    REFERENCE_ONLY,
    REPLAY_AUTHORITY,
    RUNTIME_AUTHORITY,
    RUNTIME_DEPENDENCY,
    VALIDATION_AUTHORITY,
    DISPLAY_ONLY,
    EXECUTION_AUTHORITY,
    ADMISSIBILITY_AUTHORITY,
    constitutional_afripower_metadata,
    assert_afripower_constitution,
)
from afritech.afripower.graph_projection import build_graph_projection
from afritech.afripower.projection_models import build_afripower_projection_dict


VALIDATOR_NAME = "afritech.ci.afripower_intelligence_validator"

AFRIPOWER_ROOT = Path("afritech/afripower")
AFRIPOWER_TEST_ROOT = Path("afritech/tests/afripower")

REQUIRED_IMPLEMENTATION_FILES: tuple[Path, ...] = (
    AFRIPOWER_ROOT / "__init__.py",
    AFRIPOWER_ROOT / "constants.py",
    AFRIPOWER_ROOT / "projection_models.py",
    AFRIPOWER_ROOT / "graph_projection.py",
)

REQUIRED_TEST_FILES: tuple[Path, ...] = (
    AFRIPOWER_TEST_ROOT / "__init__.py",
    AFRIPOWER_TEST_ROOT / "test_constants.py",
    AFRIPOWER_TEST_ROOT / "test_projection_models.py",
    AFRIPOWER_TEST_ROOT / "test_graph_projection.py",
    AFRIPOWER_TEST_ROOT / "test_afripower_intelligence_validator.py",
)

AUTHORITY_FLAGS: tuple[tuple[str, bool], ...] = (
    ("RUNTIME_AUTHORITY", RUNTIME_AUTHORITY),
    ("ENFORCEMENT_AUTHORITY", ENFORCEMENT_AUTHORITY),
    ("VALIDATION_AUTHORITY", VALIDATION_AUTHORITY),
    ("REPLAY_AUTHORITY", REPLAY_AUTHORITY),
    ("PROOF_AUTHORITY", PROOF_AUTHORITY),
    ("CI_AUTHORITY", CI_AUTHORITY),
    ("GOVERNANCE_AUTHORITY", GOVERNANCE_AUTHORITY),
    ("DECISION_AUTHORITY", DECISION_AUTHORITY),
    ("ADMISSIBILITY_AUTHORITY", ADMISSIBILITY_AUTHORITY),
    ("INTELLIGENCE_AUTHORITY", INTELLIGENCE_AUTHORITY),
    ("EXECUTION_AUTHORITY", EXECUTION_AUTHORITY),
    ("AUTHORITATIVE", AUTHORITATIVE),
    ("PROJECTION_CREATES_AUTHORITY", PROJECTION_CREATES_AUTHORITY),
)

MUTATION_FLAGS: tuple[tuple[str, bool], ...] = (
    ("MUTATION_ALLOWED", MUTATION_ALLOWED),
    ("RECEIPT_MUTATION_ALLOWED", RECEIPT_MUTATION_ALLOWED),
    ("PROOF_MUTATION_ALLOWED", PROOF_MUTATION_ALLOWED),
    ("GOVERNANCE_MUTATION_ALLOWED", GOVERNANCE_MUTATION_ALLOWED),
    ("RUNTIME_DEPENDENCY", RUNTIME_DEPENDENCY),
)

SAFETY_FLAGS: tuple[tuple[str, bool], ...] = (
    ("REFERENCE_ONLY", REFERENCE_ONLY),
    ("READ_ONLY", READ_ONLY),
    ("DISPLAY_ONLY", DISPLAY_ONLY),
    ("OBSERVATIONAL_ONLY", OBSERVATIONAL_ONLY),
    ("PROJECTION_ONLY", PROJECTION_ONLY),
    ("ENTERPRISE_INTELLIGENCE_ONLY", ENTERPRISE_INTELLIGENCE_ONLY),
)

LAW_FLAGS: tuple[tuple[str, bool], ...] = (
    ("LAW_AFRIPOWER_IS_READ_ONLY", LAW_AFRIPOWER_IS_READ_ONLY),
    ("LAW_AFRIPOWER_IS_NON_AUTHORITATIVE", LAW_AFRIPOWER_IS_NON_AUTHORITATIVE),
    ("LAW_AFRIPOWER_IS_DISPLAY_ONLY", LAW_AFRIPOWER_IS_DISPLAY_ONLY),
    (
        "LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY",
        LAW_AFRIPOWER_CONSUMES_AUTHORITY_ONLY,
    ),
    (
        "LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE",
        LAW_AFRIPOWER_CANNOT_CREATE_AUTHORITY_SURFACE,
    ),
    (
        "LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME",
        LAW_AFRIPOWER_CANNOT_INFLUENCE_RUNTIME,
    ),
    (
        "LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY",
        LAW_AFRIPOWER_CANNOT_INFLUENCE_REPLAY,
    ),
    (
        "LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF",
        LAW_AFRIPOWER_CANNOT_INFLUENCE_PROOF,
    ),
    ("LAW_AFRIPOWER_CANNOT_INFLUENCE_CI", LAW_AFRIPOWER_CANNOT_INFLUENCE_CI),
    (
        "LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE",
        LAW_AFRIPOWER_CANNOT_INFLUENCE_GOVERNANCE,
    ),
)


class AFRIPowerValidationError(RuntimeError):
    """Raised when AFRIPower violates its intelligence boundary."""


def _missing_files(paths: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(path for path in paths if not path.is_file())


def validate_required_files() -> None:
    missing = _missing_files(REQUIRED_IMPLEMENTATION_FILES)

    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise AFRIPowerValidationError(
            f"missing AFRIPower implementation files: {formatted}"
        )


def validate_required_tests() -> None:
    missing = _missing_files(REQUIRED_TEST_FILES)

    if missing:
        formatted = ", ".join(str(path) for path in missing)
        raise AFRIPowerValidationError(
            f"missing AFRIPower test files: {formatted}"
        )


def validate_identity() -> None:
    if AFRIPOWER_COMPONENT != "AFRIPower":
        raise AFRIPowerValidationError("invalid AFRIPower component identity")

    if AFRIPOWER_COMPONENT_ID != "afritech.afripower":
        raise AFRIPowerValidationError("invalid AFRIPower component id")

    if AFRIPOWER_PROJECTION_STATUS != "ENTERPRISE_INTELLIGENCE_PROJECTION":
        raise AFRIPowerValidationError("invalid AFRIPower projection status")

    if INTELLIGENCE_STATUS != "READ_ONLY_ENTERPRISE_INTELLIGENCE":
        raise AFRIPowerValidationError("invalid AFRIPower intelligence status")


def validate_no_authority() -> None:
    violations = tuple(name for name, value in AUTHORITY_FLAGS if value is not False)

    if violations:
        raise AFRIPowerValidationError(
            "AFRIPower authority flags must remain false: "
            + ", ".join(violations)
        )


def validate_no_mutation() -> None:
    violations = tuple(name for name, value in MUTATION_FLAGS if value is not False)

    if violations:
        raise AFRIPowerValidationError(
            "AFRIPower mutation flags must remain false: "
            + ", ".join(violations)
        )


def validate_safety_flags() -> None:
    violations = tuple(name for name, value in SAFETY_FLAGS if value is not True)

    if violations:
        raise AFRIPowerValidationError(
            "AFRIPower safety flags must remain true: "
            + ", ".join(violations)
        )


def validate_law_flags() -> None:
    violations = tuple(name for name, value in LAW_FLAGS if value is not True)

    if violations:
        raise AFRIPowerValidationError(
            "AFRIPower constitutional law flags must remain true: "
            + ", ".join(violations)
        )


def validate_metadata_contract() -> None:
    metadata = constitutional_afripower_metadata()

    required_false = (
        "runtime_authority",
        "enforcement_authority",
        "validation_authority",
        "replay_authority",
        "proof_authority",
        "ci_authority",
        "governance_authority",
        "decision_authority",
        "admissibility_authority",
        "intelligence_authority",
        "execution_authority",
        "authoritative",
        "mutation_allowed",
        "receipt_mutation_allowed",
        "proof_mutation_allowed",
        "governance_mutation_allowed",
        "runtime_dependency",
        "projection_creates_authority",
    )

    for key in required_false:
        if metadata.get(key) is not False:
            raise AFRIPowerValidationError(
                f"AFRIPower metadata field must be false: {key}"
            )

    required_true = (
        "reference_only",
        "read_only",
        "display_only",
        "observational_only",
        "projection_only",
        "enterprise_intelligence_only",
        "law_read_only",
        "law_non_authoritative",
        "law_display_only",
        "law_consumes_authority_only",
        "law_cannot_create_authority_surface",
        "law_cannot_influence_runtime",
        "law_cannot_influence_replay",
        "law_cannot_influence_proof",
        "law_cannot_influence_ci",
        "law_cannot_influence_governance",
    )

    for key in required_true:
        if metadata.get(key) is not True:
            raise AFRIPowerValidationError(
                f"AFRIPower metadata field must be true: {key}"
            )


def validate_projection_contracts() -> None:
    payloads = (
        {
            "execution_id": "exec.afripower.validator.001",
            "traceability": (
                {"type": "ADR", "id": "ADR-AFRIPOWER-READ-ONLY"},
                {"type": "Invariant", "id": "INVARIANT-AFRIPOWER-NO-AUTHORITY"},
                {"type": "Proof", "id": "PROOF-AFRIPOWER-REFERENCE-ONLY"},
            ),
        },
    )

    graph_projection = build_graph_projection(payloads)
    model_projection = build_afripower_projection_dict(payloads)

    for projection_name, projection in (
        ("graph_projection", graph_projection),
        ("model_projection", model_projection),
    ):
        if projection.get("read_only") is not True:
            raise AFRIPowerValidationError(
                f"{projection_name} must remain read-only"
            )

        if projection.get("reference_only") is not True:
            raise AFRIPowerValidationError(
                f"{projection_name} must remain reference-only"
            )

        if projection.get("display_only") is not True:
            raise AFRIPowerValidationError(
                f"{projection_name} must remain display-only"
            )

        if projection.get("creates_authority") is not False:
            raise AFRIPowerValidationError(
                f"{projection_name} must not create authority"
            )

        if projection.get("runtime_authority") is not False:
            raise AFRIPowerValidationError(
                f"{projection_name} must not have runtime authority"
            )

        if projection.get("validation_authority") is not False:
            raise AFRIPowerValidationError(
                f"{projection_name} must not have validation authority"
            )

        if projection.get("governance_authority") is not False:
            raise AFRIPowerValidationError(
                f"{projection_name} must not have governance authority"
            )

        nodes = projection.get("nodes")
        edges = projection.get("edges")

        if not isinstance(nodes, list) or not nodes:
            raise AFRIPowerValidationError(
                f"{projection_name} must produce projection nodes"
            )

        if not isinstance(edges, list) or not edges:
            raise AFRIPowerValidationError(
                f"{projection_name} must produce projection edges"
            )


def validate_afripower_intelligence_surface(
    *,
    require_tests: bool = False,
) -> None:
    validate_required_files()

    if require_tests:
        validate_required_tests()

    validate_identity()
    validate_no_authority()
    validate_no_mutation()
    validate_safety_flags()
    validate_law_flags()
    validate_metadata_contract()
    validate_projection_contracts()
    assert_afripower_constitution()


def run_validation(argv: Sequence[str] | None = None) -> int:
    args = tuple(argv if argv is not None else sys.argv[1:])
    require_tests = "--require-tests" in args

    try:
        validate_afripower_intelligence_surface(require_tests=require_tests)
    except AFRIPowerValidationError as exc:
        print(f"❌ AFRIPower intelligence validation FAILED: {exc}")
        return 1
    except Exception as exc:  # defensive fail-closed CI boundary
        print(f"❌ AFRIPower intelligence validation FAILED: {exc}")
        return 1

    print("✅ AFRIPower intelligence validation PASSED")
    return 0


def main() -> int:
    return run_validation()


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AFRIPowerValidationError",
    "VALIDATOR_NAME",
    "REQUIRED_IMPLEMENTATION_FILES",
    "REQUIRED_TEST_FILES",
    "validate_required_files",
    "validate_required_tests",
    "validate_identity",
    "validate_no_authority",
    "validate_no_mutation",
    "validate_safety_flags",
    "validate_law_flags",
    "validate_metadata_contract",
    "validate_projection_contracts",
    "validate_afripower_intelligence_surface",
    "run_validation",
    "main",
]
