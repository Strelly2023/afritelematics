from __future__ import annotations

from .models import VisualBaseline, VisualRegressionResult


def verify_visual_regression(baseline: VisualBaseline | None, *, tool_ran: bool, screens_checked: int = 0, regressions: int = 0, unapproved_differences: int = 0) -> VisualRegressionResult:
    approved = bool(baseline and baseline.state == "APPROVED")
    verified = bool(tool_ran and approved and screens_checked > 0 and regressions == 0 and unapproved_differences == 0)
    return VisualRegressionResult(True, tool_ran, verified, approved, screens_checked, regressions, unapproved_differences)
