from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RuleResult:
    name: str
    passed: bool
    issues: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "issues": list(self.issues),
        }


def pass_or_fail(name: str, issues: list[str]) -> RuleResult:
    return RuleResult(name=name, passed=not issues, issues=tuple(issues))
