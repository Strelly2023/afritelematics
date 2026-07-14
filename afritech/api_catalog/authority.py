"""Authority metadata helpers."""

from __future__ import annotations

from afritech.api_catalog.domains import DomainEndpoint


def authority_extension(endpoint: DomainEndpoint) -> dict[str, object]:
    return {
        "policy-engine": endpoint.authority_policy,
        "approval-required": endpoint.risk_level == "high",
        "allowed-roles": list(endpoint.allowed_roles),
    }


def evidence_extension(endpoint: DomainEndpoint) -> dict[str, object]:
    return {
        "audit-required": endpoint.audit_required,
        "replay-required": endpoint.replay_required,
        "receipt-required": endpoint.receipt_required,
    }
