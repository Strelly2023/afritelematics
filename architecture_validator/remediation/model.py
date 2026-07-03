from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AutoFix:
    rule: str
    issue: str
    fix_type: str
    action: str
    risk: str
    safe_to_apply: bool
    detail: str
    target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule,
            "issue": self.issue,
            "type": self.fix_type,
            "action": self.action,
            "risk": self.risk,
            "safe_to_apply": self.safe_to_apply,
            "detail": self.detail,
            "target": self.target,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class FixExecutionResult:
    fix: AutoFix
    status: str
    message: str
    artifact: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "fix": self.fix.as_dict(),
            "status": self.status,
            "message": self.message,
            "artifact": self.artifact,
        }
