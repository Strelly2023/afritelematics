"""Enforce AfriTech test-contract coverage across a test root."""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEST_ROOT = ROOT / "afritech/tests/compliance"

REQUIRED_TEST_PATTERNS: tuple[str, ...] = (
    "test_happy_path",
    "test_invalid_input",
    "test_determinism",
    "test_replay_stability",
    "test_tampering",
    "test_serialization",
    "test_schema",
    "test_authority_boundary",
    "test_governance",
    "test_backward_compatibility",
    "test_detects_drift",
    "test_reproducibility",
)


class TestContractEnforcementGuardError(RuntimeError):
    """Raised when the test-contract coverage is incomplete."""


@dataclass(frozen=True)
class TestContractEnforcementReport:
    root: str
    file_count: int
    test_function_count: int
    pattern_hits: dict[str, int]
    missing_patterns: tuple[str, ...]
    parse_errors: tuple[str, ...]

    @property
    def verified(self) -> bool:
        return (
            self.file_count > 0
            and self.test_function_count > 0
            and not self.missing_patterns
            and not self.parse_errors
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "file_count": self.file_count,
            "test_function_count": self.test_function_count,
            "pattern_hits": dict(sorted(self.pattern_hits.items())),
            "missing_patterns": list(self.missing_patterns),
            "parse_errors": list(self.parse_errors),
            "verified": self.verified,
        }


def validate(root: Path = DEFAULT_TEST_ROOT) -> TestContractEnforcementReport:
    root = root.resolve()
    if not root.exists():
        raise TestContractEnforcementGuardError(f"test root does not exist: {root}")
    if not root.is_dir():
        raise TestContractEnforcementGuardError(f"test root must be a directory: {root}")

    test_files = sorted(path for path in root.rglob("test_*.py") if path.is_file())
    if not test_files:
        raise TestContractEnforcementGuardError(f"no test files found under: {root}")

    parse_errors: list[str] = []
    all_functions: set[str] = set()

    for path in test_files:
        try:
            all_functions.update(_find_test_functions(path))
        except SyntaxError as exc:
            parse_errors.append(f"{path}: {exc.msg}")

    pattern_hits = {
        pattern: sum(1 for fn in all_functions if pattern in fn)
        for pattern in REQUIRED_TEST_PATTERNS
    }
    missing_patterns = tuple(pattern for pattern, count in pattern_hits.items() if count == 0)

    report = TestContractEnforcementReport(
        root=str(root),
        file_count=len(test_files),
        test_function_count=len(all_functions),
        pattern_hits=pattern_hits,
        missing_patterns=missing_patterns,
        parse_errors=tuple(parse_errors),
    )
    if not report.verified:
        details = []
        if report.missing_patterns:
            details.append(f"missing patterns: {', '.join(report.missing_patterns)}")
        if report.parse_errors:
            details.append(f"parse errors: {', '.join(report.parse_errors)}")
        raise TestContractEnforcementGuardError(
            "test contract enforcement failed: " + "; ".join(details)
        )
    return report


def run_test_contract_guard(root: Path = DEFAULT_TEST_ROOT) -> TestContractEnforcementReport:
    return validate(root=root)


def _find_test_functions(file_path: Path) -> set[str]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            functions.add(node.name)
    return functions


def _format_report(report: TestContractEnforcementReport) -> str:
    pattern_summary = ", ".join(
        f"{pattern}={report.pattern_hits.get(pattern, 0)}" for pattern in REQUIRED_TEST_PATTERNS
    )
    return (
        "TEST_CONTRACT_ENFORCEMENT: PASS "
        f"(root={report.root}, files={report.file_count}, tests={report.test_function_count}, "
        f"patterns=[{pattern_summary}])"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_TEST_ROOT,
        help="Test root to scan for contract coverage.",
    )
    args = parser.parse_args(argv)

    try:
        report = validate(root=args.root)
    except TestContractEnforcementGuardError as exc:
        print(f"TEST_CONTRACT_ENFORCEMENT: FAIL ({exc})")
        raise SystemExit(1)

    print(_format_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
