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

from typing import Iterable
from afritech.verify.engine import ReplayResult


# ---------------------------------------------------------------------
# Reporting helpers
# ---------------------------------------------------------------------

def _print_violations(violations: Iterable[str]) -> None:
    print()
    print("❌ REPLAY VIOLATIONS DETECTED")
    for idx, violation in enumerate(violations, start=1):
        print(f"  {idx}. {violation}")


def _print_success(terminal_epoch: int) -> None:
    print()
    print("✅ Replay valid")
    print(f"✅ Terminal epoch: {terminal_epoch}")
    print("✅ Constitutional lineage intact")


# ---------------------------------------------------------------------
# Public report API
# ---------------------------------------------------------------------

def print_report(result: ReplayResult) -> None:
    """
    Print a human-readable replay verification report.

    Args:
        result: ReplayResult returned by verify_replay()
    """
    if result.valid:
        _print_success(result.terminal_epoch)
    else:
        print()
        print("❌ REPLAY INVALID")
        if result.terminal_epoch is not None:
            print(f"❌ Terminal epoch: {result.terminal_epoch}")
        _print_violations(result.violations)