"""Policy evaluation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass
class PolicyDecision:
    allowed: bool
    code: str
    reason: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)


class PolicyEvaluator:
    def evaluate(self, policy_code: str | None, *, context: Mapping[str, Any], definition: Mapping[str, Any] | None = None) -> PolicyDecision:
        if policy_code is None:
            return PolicyDecision(True, code="POLICY_NOT_REQUIRED")
        if context.get("purpose") in {definition.get("purpose") if definition else None, policy_code}:
            return PolicyDecision(True, code="POLICY_APPROVED")
        return PolicyDecision(False, code="POLICY_DENIED", reason="purpose_mismatch")
