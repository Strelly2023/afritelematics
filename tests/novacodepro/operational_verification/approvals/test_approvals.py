import pytest

from afritech.novacodepro.operational_verification.approvals.models import ExecutiveApprovalDecision
from afritech.novacodepro.operational_verification.approvals.workflow import validate_executive_decision
from afritech.novacodepro.operational_verification.errors import ApprovalPolicyError


def test_executive_approval_requires_prr_and_four_eyes() -> None:
    decision = ExecutiveApprovalDecision("approval-1", "approver", "CTO", "APPROVE", "low", "hash")

    with pytest.raises(ApprovalPolicyError):
        validate_executive_decision(decision, prr_approved=False, creator_id="creator")
    with pytest.raises(ApprovalPolicyError):
        validate_executive_decision(decision, prr_approved=True, creator_id="approver")

    result = validate_executive_decision(decision, prr_approved=True, creator_id="creator")
    assert result["executive_approved"] is True
    assert result["ga_allowed"] is False
