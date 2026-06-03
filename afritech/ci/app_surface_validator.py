"""
Constitutional App Surface Validator

Purpose
-------
Validate that application surfaces remain interface-only.

Applications may:
    - display
    - request
    - confirm
    - explain
    - replay

Applications must not:
    - own pricing authority
    - own dispatch authority
    - mutate replay
    - bypass API boundaries
    - import runtime authority directly
    - access databases directly
    - perform ranking/allocation decisions

This validator is intentionally fail-closed.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final


APP_SURFACES: Final[tuple[str, ...]] = (
    "rider_app",
    "driver_app",
    "desktop_app",
    "web_app",
)

CHECK_EXTENSIONS: Final[set[str]] = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".kt",
    ".java",
    ".swift",
    ".dart",
}

EXCLUDED_DIRS: Final[set[str]] = {
    ".expo",
    ".git",
    ".next",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
}

FORBIDDEN_PATTERNS: Final[
    tuple[tuple[str, re.Pattern[str]], ...]
] = (
    (
        "pricing_logic_in_app",
        re.compile(
            r"\b("
            r"base_fare|"
            r"surge|"
            r"price_multiplier|"
            r"calculate_price|"
            r"fare_formula|"
            r"dynamic_pricing|"
            r"compute_fare|"
            r"pricing_engine"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "dispatch_logic_in_app",
        re.compile(
            r"\b("
            r"assign_driver|"
            r"match_driver|"
            r"rank_driver|"
            r"driver_ranking|"
            r"dispatch_score|"
            r"allocation_score|"
            r"best_driver|"
            r"nearest_driver_selection"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "replay_mutation_from_app",
        re.compile(
            r"\b("
            r"mutate_replay|"
            r"update_replay|"
            r"delete_replay|"
            r"write_replay|"
            r"replay_store\.save|"
            r"replay_store\.write"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "direct_runtime_import",
        re.compile(
            r"\b("
            r"from\s+afritech\.(runtime|engine)|"
            r"import\s+afritech\.(runtime|engine)"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "direct_database_import",
        re.compile(
            r"\b("
            r"from\s+afritech\.(database|db)|"
            r"import\s+afritech\.(database|db)"
            r")",
            re.IGNORECASE,
        ),
    ),
    (
        "direct_sql_usage",
        re.compile(
            r"\b("
            r"SELECT\s+|"
            r"INSERT\s+|"
            r"UPDATE\s+|"
            r"DELETE\s+FROM"
            r")",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class Violation:
    surface: str
    file_path: str
    rule: str
    line_number: int
    line: str


@dataclass(frozen=True)
class ValidationSummary:
    files_checked: int
    surfaces_checked: int
    violations: int


def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts)


def iter_app_files(root: Path) -> list[Path]:
    files: list[Path] = []

    for surface in APP_SURFACES:
        surface_path = root / surface

        if not surface_path.exists():
            continue

        for path in surface_path.rglob("*"):
            if is_excluded(path):
                continue

            if path.is_file() and path.suffix in CHECK_EXTENSIONS:
                files.append(path)

    return sorted(files)


def validate_file(root: Path, path: Path) -> list[Violation]:
    violations: list[Violation] = []

    try:
        lines = path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()
    except OSError:
        return violations

    surface = path.relative_to(root).parts[0]

    for line_number, line in enumerate(lines, start=1):
        for rule, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                violations.append(
                    Violation(
                        surface=surface,
                        file_path=str(path.relative_to(root)),
                        rule=rule,
                        line_number=line_number,
                        line=line.strip(),
                    )
                )

    return violations


def validate_app_surfaces(
    root: Path,
) -> tuple[list[Violation], ValidationSummary]:
    violations: list[Violation] = []

    files = iter_app_files(root)

    for file_path in files:
        violations.extend(
            validate_file(root, file_path)
        )

    summary = ValidationSummary(
        files_checked=len(files),
        surfaces_checked=len(APP_SURFACES),
        violations=len(violations),
    )

    return violations, summary


def print_pass(summary: ValidationSummary) -> None:
    print("✅ App surface validation PASSED")
    print(
        f"✅ Checked surfaces: "
        f"{', '.join(APP_SURFACES)}"
    )
    print(
        f"✅ Files checked: "
        f"{summary.files_checked}"
    )
    print(
        f"✅ Violations: "
        f"{summary.violations}"
    )


def print_fail(
    violations: list[Violation],
    summary: ValidationSummary,
) -> None:
    print("❌ App surface validation FAILED")
    print(
        f"❌ Violations: "
        f"{summary.violations}"
    )

    for violation in violations:
        print(
            f"{violation.file_path}:"
            f"{violation.line_number} "
            f"[{violation.rule}] "
            f"{violation.line}"
        )


def main() -> int:
    root = Path.cwd()

    violations, summary = validate_app_surfaces(root)

    if violations:
        print_fail(
            violations,
            summary,
        )
        return 1

    print_pass(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())