from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutiveApprovalRequest:
    approval_id: str
    release_id: str
    prr_id: str
    requested_by: str
    evidence_package_hash: str
    status: str = "APPROVAL_PENDING"


@dataclass(frozen=True, slots=True)
class ExecutiveApprovalDecision:
    approval_id: str
    approver_id: str
    approver_role: str
    decision: str
    risk_summary: str
    evidence_package_hash: str
    conditions: tuple[str, ...] = ()
    scope: dict[str, object] = field(default_factory=dict)
