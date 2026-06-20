from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskResult:
    risk_score: int
    risk_level: str
    findings: tuple[str, ...]


class RiskEngine:
    def compute(
        self,
        *,
        trust_score: int,
        proof_coverage: int,
        policy_compliance: int,
        audit_integrity: int,
        receipts_present: bool,
    ) -> RiskResult:
        score = 100 - trust_score
        score += max(0, 90 - proof_coverage) // 3
        score += max(0, 90 - policy_compliance) // 4
        score += max(0, 100 - audit_integrity) // 2
        if not receipts_present:
            score += 10
        score = max(0, min(100, score))
        if score >= 75:
            level = "CRITICAL"
        elif score >= 45:
            level = "HIGH"
        elif score >= 20:
            level = "MEDIUM"
        else:
            level = "LOW"
        findings = []
        if not receipts_present:
            findings.append("deployment receipt missing")
        if audit_integrity < 100:
            findings.append("audit chain not perfectly intact")
        if proof_coverage < 80:
            findings.append("proof coverage below target")
        return RiskResult(risk_score=score, risk_level=level, findings=tuple(findings))
