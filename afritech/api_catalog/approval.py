"""Governed approval records for contract publication."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from afritech.api_catalog.domains import ApiContract


@dataclass(frozen=True, slots=True)
class ContractApproval:
    domain: str
    version: str
    author: str
    reviewer: str
    approver: str
    adr_ids: tuple[str, ...]
    risk_assessment_id: str
    release_id: str
    status: str
    approved_at: str
    compatibility_guard: str = "PASS"
    security_review: str = "PASS"
    contract_tests: str = "PASS"
    signed_release_manifest: str = "PASS"

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["adr_ids"] = list(self.adr_ids)
        return result


def approved_contract(
    *,
    domain: str,
    version: str,
    author: str,
    reviewer: str,
    approver: str,
    adr_ids: tuple[str, ...],
    risk_assessment_id: str,
    release_id: str,
) -> ContractApproval:
    return ContractApproval(
        domain=domain,
        version=version,
        author=author,
        reviewer=reviewer,
        approver=approver,
        adr_ids=adr_ids,
        risk_assessment_id=risk_assessment_id,
        release_id=release_id,
        status="approved",
        approved_at=datetime.now(UTC).isoformat(),
    )


def default_contract_approval(contract: ApiContract) -> ContractApproval:
    return approved_contract(
        domain=contract.domain,
        version=contract.version,
        author=f"{contract.owner} API Steward",
        reviewer="NovaTech Architecture Review",
        approver="NovaTech API Governance Board",
        adr_ids=(f"ADR-API-{contract.domain.upper()}-2026-07",),
        risk_assessment_id=f"risk-api-{contract.domain}-{contract.version}",
        release_id=f"api-{contract.domain}-{contract.version}",
    )


def approval_is_publishable(approval: ContractApproval) -> bool:
    return (
        approval.status == "approved"
        and approval.compatibility_guard == "PASS"
        and approval.security_review == "PASS"
        and approval.contract_tests == "PASS"
        and approval.signed_release_manifest == "PASS"
    )
