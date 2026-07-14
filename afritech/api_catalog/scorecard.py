"""API quality and governance scorecard."""

from __future__ import annotations

from typing import Any

from afritech.api_catalog.compatibility import lint_contract
from afritech.api_catalog.domains import ApiContract


def contract_scorecard(contract: ApiContract) -> dict[str, Any]:
    total = len(contract.endpoints)
    if total == 0:
        return {"domain": contract.domain, "score": 0, "status": "FAILED"}
    versioned = total
    described = sum(1 for endpoint in contract.endpoints if endpoint.summary.strip())
    authority_bound = sum(1 for endpoint in contract.endpoints if endpoint.allowed_roles or "public" in endpoint.audience)
    replay_covered = sum(1 for endpoint in contract.endpoints if isinstance(endpoint.replay_required, bool))
    idempotency_compliant = sum(
        1
        for endpoint in contract.endpoints
        if endpoint.method.upper() == "GET" or endpoint.risk_level != "high" or endpoint.idempotency_required
    )
    lint_issues = len(lint_contract(contract))
    metrics = {
        "versioned_contract_pct": round(versioned / total * 100, 2),
        "description_coverage_pct": round(described / total * 100, 2),
        "authority_coverage_pct": round(authority_bound / total * 100, 2),
        "replay_coverage_pct": round(replay_covered / total * 100, 2),
        "idempotency_compliance_pct": round(idempotency_compliant / total * 100, 2),
        "lint_issue_count": lint_issues,
    }
    score = round(
        (
            metrics["versioned_contract_pct"]
            + metrics["description_coverage_pct"]
            + metrics["authority_coverage_pct"]
            + metrics["replay_coverage_pct"]
            + metrics["idempotency_compliance_pct"]
        )
        / 5
        - min(lint_issues * 2, 20),
        2,
    )
    return {"domain": contract.domain, "version": contract.version, "score": max(score, 0), "status": "PASS" if score >= 90 and lint_issues == 0 else "REVIEW", "metrics": metrics}
