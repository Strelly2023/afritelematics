# afritech/verify/report.py

from __future__ import annotations

"""
AfriTech Constitutional Replay Report
====================================

Human- and CI-friendly reporting for replay verification results.

This module:
- Formats replay verification output
- Does NOT perform verification
- Does NOT mutate state
- Does NOT enforce policy
"""

from typing import Iterable, List
from afritech.verify.engine import ReplayResult


# ---------------------------------------------------------------------
# SAFE ACCESS HELPERS (COMPATIBILITY)
# ---------------------------------------------------------------------

def _get_violations(result: ReplayResult) -> List[str]:
    """
    Normalize violation sources across versions.
    """

    if hasattr(result, "violations") and result.violations:
        return list(result.violations)

    if hasattr(result, "errors") and result.errors:
        return list(result.errors)

    return []


def _get_terminal_epoch(result: ReplayResult):
    return getattr(result, "terminal_epoch", None)


# ---------------------------------------------------------------------
# REPORTING HELPERS
# ---------------------------------------------------------------------

def _print_violations(violations: Iterable[str]) -> None:
    print()
    print("❌ REPLAY VIOLATIONS DETECTED")

    for idx, violation in enumerate(violations, start=1):
        print(f"  {idx}. {violation}")


def _print_success(terminal_epoch: int | None) -> None:
    print()
    print("✅ Replay valid")

    if terminal_epoch is not None:
        print(f"✅ Terminal epoch: {terminal_epoch}")

    print("✅ Constitutional lineage intact")


def _print_failure(result: ReplayResult) -> None:
    print()
    print("❌ REPLAY INVALID")

    terminal_epoch = _get_terminal_epoch(result)

    if terminal_epoch is not None:
        print(f"❌ Terminal epoch: {terminal_epoch}")

    violations = _get_violations(result)

    if violations:
        _print_violations(violations)
    else:
        print("⚠️ No explicit violations reported")


# ---------------------------------------------------------------------
# PUBLIC REPORT API
# ---------------------------------------------------------------------

def print_report(result: ReplayResult) -> None:
    """
    Print a human-readable replay verification report.

    This function is strictly observational:
    - no mutation
    - no validation
    - no execution

    Args:
        result: ReplayResult returned by verify_replay()
    """

    if getattr(result, "valid", False):
        _print_success(_get_terminal_epoch(result))
    else:
        _print_failure(result)