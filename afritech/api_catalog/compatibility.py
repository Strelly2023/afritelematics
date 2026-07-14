"""API contract linting and compatibility checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from afritech.api_catalog.domains import ApiContract


@dataclass(frozen=True, slots=True)
class CatalogIssue:
    code: str
    domain: str
    path: str | None
    message: str


def lint_contract(contract: ApiContract) -> list[CatalogIssue]:
    issues: list[CatalogIssue] = []
    for endpoint in contract.endpoints:
        if not endpoint.summary:
            issues.append(CatalogIssue("MISSING_DESCRIPTION", contract.domain, endpoint.path, "endpoint summary is required"))
        if not endpoint.operation_id:
            issues.append(CatalogIssue("MISSING_OPERATION_ID", contract.domain, endpoint.path, "operationId is required"))
        if endpoint.risk_level == "high" and endpoint.method in {"POST", "PUT", "PATCH", "DELETE"} and not endpoint.idempotency_required:
            issues.append(CatalogIssue("MISSING_IDEMPOTENCY", contract.domain, endpoint.path, "high-risk writes require idempotency"))
        if endpoint.risk_level == "high" and not endpoint.allowed_roles:
            issues.append(CatalogIssue("MISSING_AUTHORITY", contract.domain, endpoint.path, "high-risk endpoints require roles"))
        if endpoint.deprecated and not endpoint.replaced_by:
            issues.append(CatalogIssue("MISSING_DEPRECATION_MIGRATION", contract.domain, endpoint.path, "deprecated endpoint needs replacement"))
        if "public" in endpoint.audience and endpoint.allowed_roles and any(role in {"ADMIN", "INTERNAL"} for role in endpoint.allowed_roles):
            issues.append(CatalogIssue("PUBLIC_INTERNAL_ROLE", contract.domain, endpoint.path, "public endpoint exposes internal role"))
    return issues


def compatibility_summary(contracts: tuple[ApiContract, ...]) -> dict[str, object]:
    issues = [issue for contract in contracts for issue in lint_contract(contract)]
    return {
        "status": "PASS" if not issues else "FAIL",
        "checked_domains": [contract.domain for contract in contracts],
        "issue_count": len(issues),
        "issues": [asdict(issue) for issue in issues],
        "stable_breaking_change_policy": "response field removal is forbidden for stable APIs",
        "authority_change_policy": "authority changes require explicit review",
    }
