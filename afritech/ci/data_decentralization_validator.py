"""Validate governed data decentralization without booting runtime surfaces."""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATA_GOVERNANCE_ROOT = ROOT / "afritech/data_governance"
GOVERNANCE_RULE = ROOT / "afritech/governance/rules/RULE-040-data-decentralization.yaml"
GOVERNANCE_BINDING = ROOT / "afritech/governance/bindings/BIND-020-data-decentralization.yaml"
ADR = ROOT / "afritech/governance/adr/ADR-0020-data-decentralization.yaml"
TEST_FILE = ROOT / "afritech/tests/ci/test_data_decentralization_validator.py"

REQUIRED_FILES = (
    DATA_GOVERNANCE_ROOT / "__init__.py",
    DATA_GOVERNANCE_ROOT / "contracts.py",
    DATA_GOVERNANCE_ROOT / "ownership.py",
    DATA_GOVERNANCE_ROOT / "guards.py",
    DATA_GOVERNANCE_ROOT / "registry.py",
    GOVERNANCE_RULE,
    GOVERNANCE_BINDING,
    ADR,
    TEST_FILE,
)

FORBIDDEN_TEXT = (
    ".objects.get(",
    ".objects.filter(",
    "select_related(",
    "prefetch_related(",
    "raw(",
    "connection.cursor(",
)


class DataDecentralizationValidationError(RuntimeError):
    """Raised when data decentralization governance is broken."""


def validate() -> bool:
    _validate_required_files()
    _validate_registry_source()
    _validate_guard_source()
    _validate_no_runtime_database_access()
    _validate_governance_chain()
    return True


def _validate_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not path.exists()]
    if missing:
        raise DataDecentralizationValidationError(
            "missing data decentralization files: " + ", ".join(map(str, missing))
        )


def _validate_registry_source() -> None:
    source = (DATA_GOVERNANCE_ROOT / "registry.py").read_text(encoding="utf-8")
    for needle in (
        "INV_DATA_001",
        "DATA_DECENTRALIZATION_STATUS",
        "GOVERNED_DECENTRALIZATION_DEFINED",
        "validate_data_governance_registry",
        "direct database sharing is forbidden",
    ):
        if needle not in source:
            raise DataDecentralizationValidationError(
                f"registry missing required text: {needle}"
            )


def _validate_guard_source() -> None:
    source = (DATA_GOVERNANCE_ROOT / "guards.py").read_text(encoding="utf-8")
    for needle in (
        "guard_owner_domain",
        "guard_data_write",
        "guard_cross_domain_access",
        "only owner domain may write owned data",
        "direct cross-domain database access is forbidden",
    ):
        if needle not in source:
            raise DataDecentralizationValidationError(
                f"guards missing required text: {needle}"
            )


def _validate_no_runtime_database_access() -> None:
    for path in sorted(DATA_GOVERNANCE_ROOT.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_TEXT:
            if forbidden in source:
                raise DataDecentralizationValidationError(
                    f"{path} contains forbidden runtime database access: {forbidden}"
                )
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "django"
            ):
                raise DataDecentralizationValidationError(
                    f"{path} imports Django runtime surface"
                )


def _validate_governance_chain() -> None:
    adr = ADR.read_text(encoding="utf-8")
    rule = GOVERNANCE_RULE.read_text(encoding="utf-8")
    binding = GOVERNANCE_BINDING.read_text(encoding="utf-8")
    tests = TEST_FILE.read_text(encoding="utf-8")
    for needle in (
        "ADR-0020",
        "INV-DATA-001",
        "RULE-040",
        "BIND-020",
        "data_decentralization_validator",
    ):
        if needle not in f"{adr}\n{rule}\n{binding}\n{tests}":
            raise DataDecentralizationValidationError(
                f"governance chain missing: {needle}"
            )


def main() -> int:
    try:
        validate()
    except DataDecentralizationValidationError as exc:
        print(f"Data decentralization validation FAILED: {exc}")
        return 1
    print("Data decentralization validation PASSED")
    print("Invariant: INV-DATA-001")
    print("Status: GOVERNED_DECENTRALIZATION_DEFINED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
