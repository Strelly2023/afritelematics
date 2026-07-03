from __future__ import annotations

from typing import Any

from architecture_validator.remediation.engine import AutoFixEngine
from architecture_validator.remediation.model import AutoFix


class GovernanceAgent:
    def __init__(self, engine: AutoFixEngine | None = None) -> None:
        self.engine = engine or AutoFixEngine()

    def process(self, report: list[dict[str, Any]]) -> list[AutoFix]:
        fixes: list[AutoFix] = []
        for rule in report:
            if rule.get("passed") is True:
                continue
            rule_name = str(rule.get("name") or "Unknown Rule")
            issues = rule.get("issues") if isinstance(rule.get("issues"), list) else []
            if not issues:
                fixes.append(
                    self.engine.generate_fix(rule_name, "Rule failed without issue details")
                )
                continue
            for issue in issues:
                fixes.append(self.engine.generate_fix(rule_name, str(issue)))
        return fixes
