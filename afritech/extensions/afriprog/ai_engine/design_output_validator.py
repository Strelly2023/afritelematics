from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DesignOutputValidationResult:
    admitted: bool
    violations: tuple[str, ...]

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "admitted": self.admitted,
            "violations": list(self.violations),
            "write_enabled": False,
            "authority": "proposal_only",
        }


class DesignOutputValidator:
    """Validate structured design output without granting authority."""

    REQUIRED_SECTIONS = frozenset(
        {
            "schema",
            "format",
            "intent",
            "domain",
            "requirements",
            "architecture",
            "contracts",
            "implementation_plan",
            "evidence",
            "review",
            "write_enabled",
            "authority",
        }
    )
    REQUIRED_CONTRACTS = frozenset({"api", "database", "events"})
    FORBIDDEN_PROSE_KEYS = frozenset(
        {"text", "free_text", "markdown", "body", "content"}
    )

    def validate(self, output: Any) -> DesignOutputValidationResult:
        payload = self._payload(output)
        violations: list[str] = []

        missing = sorted(self.REQUIRED_SECTIONS - set(payload))
        if missing:
            violations.append("missing required sections: " + ", ".join(missing))

        prose_keys = sorted(self.FORBIDDEN_PROSE_KEYS.intersection(payload))
        if prose_keys:
            violations.append("forbidden prose keys present: " + ", ".join(prose_keys))

        if payload.get("schema") != "afriprog.design_output.v1":
            violations.append("schema must equal afriprog.design_output.v1")
        if payload.get("format") != "structured":
            violations.append("format must equal structured")
        if payload.get("authority") != "proposal_only":
            violations.append("authority must equal proposal_only")
        if payload.get("write_enabled") is not False:
            violations.append("write_enabled must be false")

        evidence = payload.get("evidence")
        if not isinstance(evidence, dict) or not evidence.get("evidence_id"):
            violations.append("evidence must be present")

        review = payload.get("review")
        if not isinstance(review, dict) or "admitted" not in review:
            violations.append("review must be present")

        contracts = payload.get("contracts")
        if not isinstance(contracts, dict):
            violations.append("contracts must be structured")
        else:
            missing_contracts = sorted(self.REQUIRED_CONTRACTS - set(contracts))
            if missing_contracts:
                violations.append(
                    "missing required contracts: " + ", ".join(missing_contracts)
                )

        for section in ("domain", "requirements", "architecture", "implementation_plan"):
            if section in payload and not isinstance(payload[section], dict):
                violations.append(f"{section} must be structured")

        return DesignOutputValidationResult(
            admitted=not violations,
            violations=tuple(violations),
        )

    def _payload(self, output: Any) -> dict[str, Any]:
        if hasattr(output, "canonical_dict"):
            output = output.canonical_dict()
        if not isinstance(output, dict):
            return {}
        return output
