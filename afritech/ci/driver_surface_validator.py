"""Validate that the Driver App remains an interface-only surface.

The Driver App may:
- display assigned ride evidence
- request accept/reject/start/complete through API contracts
- display receipt evidence
- display replay evidence
- display earnings evidence

The Driver App must not:
- compute pricing
- create dispatch authority
- mutate replay
- generate receipts
- authorize earnings or payouts
- bypass API/core boundaries

This validator is intentionally fail-closed and claim-bounded.
It proves only the currently tested classes of interface drift and
authority leakage are blocked.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final


DRIVER_APP_ROOT: Final[Path] = Path(
    "afriride_system/flutter/driver_app"
)

CHECK_EXTENSIONS: Final[set[str]] = {
    ".dart",
}

EXCLUDED_DIRS: Final[set[str]] = {
    ".dart_tool",
    ".flutter-plugins",
    ".flutter-plugins-dependencies",
    ".git",
    ".idea",
    ".packages",
    "build",
    "coverage",
    "ios",
    "android",
    "linux",
    "macos",
    "windows",
    "web",
}


FORBIDDEN_PATTERNS: Final[
    tuple[tuple[str, re.Pattern[str]], ...]
] = (
    (
        "local_pricing_computation",
        re.compile(
            r"\b("
            r"calculatePrice|"
            r"calculate_price|"
            r"computeFare|"
            r"compute_fare|"
            r"fareFormula|"
            r"fare_formula|"
            r"dynamicPricing|"
            r"dynamic_pricing|"
            r"surgeMultiplier|"
            r"surge_multiplier|"
            r"pricingEngine|"
            r"pricing_engine|"
            r"baseFare|"
            r"base_fare"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "replay_mutation",
        re.compile(
            r"\b("
            r"updateReplay|"
            r"update_replay|"
            r"deleteReplay|"
            r"delete_replay|"
            r"writeReplay|"
            r"write_replay|"
            r"approveReplay|"
            r"approve_replay|"
            r"overrideReplay|"
            r"override_replay|"
            r"markVerified|"
            r"mark_verified|"
            r"mutateReplay|"
            r"mutate_replay"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "dispatch_authority_creation",
        re.compile(
            r"\b("
            r"assignDriver|"
            r"assign_driver|"
            r"rankDriver|"
            r"rank_driver|"
            r"driverRanking|"
            r"driver_ranking|"
            r"matchDriver|"
            r"match_driver|"
            r"dispatchScore|"
            r"dispatch_score|"
            r"allocationScore|"
            r"allocation_score"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "receipt_generation",
        re.compile(
            r"\b("
            r"generateReceipt|"
            r"generate_receipt|"
            r"createReceipt|"
            r"create_receipt|"
            r"issueReceipt|"
            r"issue_receipt|"
            r"mintReceipt|"
            r"mint_receipt"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "earnings_authority_creation",
        re.compile(
            r"\b("
            r"authorizePayout|"
            r"authorize_payout|"
            r"settlePayout|"
            r"settle_payout|"
            r"generateEarnings|"
            r"generate_earnings|"
            r"calculateEarnings|"
            r"calculate_earnings|"
            r"computeEarnings|"
            r"compute_earnings"
            r")\b",
            re.IGNORECASE,
        ),
    ),
    (
        "direct_core_or_database_access",
        re.compile(
            r"\b("
            r"sqflite|"
            r"sqlite|"
            r"database|"
            r"directDb|"
            r"direct_db|"
            r"coreEngine|"
            r"core_engine|"
            r"runtimeEngine|"
            r"runtime_engine"
            r")\b",
            re.IGNORECASE,
        ),
    ),
)


@dataclass(frozen=True)
class Violation:
    file_path: str
    line_number: int
    rule: str
    line: str


@dataclass(frozen=True)
class ValidationSummary:
    root: str
    files_checked: int
    violations: int


def is_excluded(
    path: Path,
) -> bool:
    return any(
        part in EXCLUDED_DIRS
        for part in path.parts
    )


def iter_driver_files(
    root: Path = DRIVER_APP_ROOT,
) -> list[Path]:
    if not root.exists():
        raise FileNotFoundError(
            f"driver app root not found: {root}"
        )

    files: list[Path] = []

    for path in root.rglob("*"):
        if is_excluded(path):
            continue

        if (
            path.is_file()
            and path.suffix in CHECK_EXTENSIONS
        ):
            files.append(path)

    return sorted(files)


def validate_file(
    file_path: Path,
) -> list[Violation]:
    violations: list[Violation] = []

    lines = file_path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines()

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        for rule, pattern in FORBIDDEN_PATTERNS:
            if pattern.search(line):
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line_number=line_number,
                        rule=rule,
                        line=line.strip(),
                    )
                )

    return violations


def validate_driver_surface(
    root: Path = DRIVER_APP_ROOT,
) -> tuple[list[Violation], ValidationSummary]:
    files = iter_driver_files(root)

    violations: list[Violation] = []

    for file_path in files:
        violations.extend(
            validate_file(file_path)
        )

    summary = ValidationSummary(
        root=str(root),
        files_checked=len(files),
        violations=len(violations),
    )

    return violations, summary


def print_pass(
    summary: ValidationSummary,
) -> None:
    print("✅ Driver surface validation PASSED")
    print(f"✅ Root: {summary.root}")
    print(f"✅ Files checked: {summary.files_checked}")
    print(f"✅ Violations: {summary.violations}")


def print_fail(
    violations: list[Violation],
    summary: ValidationSummary,
) -> None:
    print("❌ Driver surface validation FAILED")
    print(f"❌ Root: {summary.root}")
    print(f"❌ Files checked: {summary.files_checked}")
    print(f"❌ Violations: {summary.violations}")

    for violation in violations:
        print(
            f"- {violation.file_path}:"
            f"{violation.line_number} "
            f"[{violation.rule}] "
            f"{violation.line}"
        )


def main() -> int:
    try:
        violations, summary = validate_driver_surface()
    except FileNotFoundError as exc:
        print("❌ Driver surface validation FAILED")
        print(f"❌ {exc}")
        return 1

    if violations:
        print_fail(violations, summary)
        return 1

    print_pass(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())