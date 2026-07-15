from __future__ import annotations

from ..errors import ApprovalPolicyError
from .models import ExecutiveApprovalDecision


EXECUTIVE_ROLES = {"CTO", "COO", "CISO", "CEO", "AUTHORIZED_EXECUTIVE"}


def validate_executive_decision(decision: ExecutiveApprovalDecision, *, prr_approved: bool, creator_id: str) -> dict[str, object]:
    if not prr_approved:
        raise ApprovalPolicyError("executive_approval_requires_prr_approval")
    if decision.approver_role not in EXECUTIVE_ROLES:
        raise ApprovalPolicyError("approver_role_not_authorized")
    if decision.approver_id == creator_id:
        raise ApprovalPolicyError("four_eyes_violation")
    return {"executive_approved": decision.decision == "APPROVE", "ga_allowed": False, "real_payments_enabled": False}
