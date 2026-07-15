from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VisualBaseline:
    baseline_id: str
    state: str
    approval_ref: str = ""


@dataclass(frozen=True, slots=True)
class VisualRegressionResult:
    configured: bool
    executed: bool
    verified: bool
    approved_baseline: bool
    screens_checked: int
    regressions: int
    unapproved_differences: int
