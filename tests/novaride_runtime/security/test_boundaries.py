from __future__ import annotations

import pytest

from afritech.guards.guard_novaride_ga_state import assert_ga_blocked
from afritech.guards.guard_novaride_offline_authority import assert_offline_operation_safe
from afritech.guards.guard_novaride_payment_boundary import assert_novaride_payment_reference_only
from afritech.guards.guard_novaride_real_payments import assert_real_payments_blocked
from afritech.guards.guard_novaride_runtime_authority import assert_frontend_not_authoritative
from afritech.novaride_runtime.common.errors import AuthorityDenied, BoundaryViolation
from afritech.novaride_runtime.models import ActorType, RuntimeContext
from afritech.novaride_runtime.services import create_runtime


def test_frontend_offline_payment_ga_and_real_payment_guards() -> None:
    with pytest.raises(PermissionError):
        assert_frontend_not_authoritative("confirmed_booking")
    with pytest.raises(PermissionError):
        assert_offline_operation_safe("payment_confirmed")
    with pytest.raises(PermissionError):
        assert_novaride_payment_reference_only("ledger_write")

    assert assert_ga_blocked() == {"GA_ALLOWED": False, "GA_APPROVAL": "PENDING"}
    assert assert_real_payments_blocked() == {
        "REAL_PAYMENTS_ENABLED": False,
        "REAL_PAYMENT_APPROVAL": "PENDING",
    }


def test_novaai_cannot_apply_operational_effect_and_operator_high_risk_needs_approval() -> None:
    runtime = create_runtime()
    ai_ctx = RuntimeContext("tenant", "org", "AU", ActorType.NOVAAI, "ai")
    operator_ctx = RuntimeContext("tenant", "org", "AU", ActorType.OPERATOR, "operator")

    with pytest.raises(BoundaryViolation):
        runtime.intelligence.apply_price(ai_ctx)
    with pytest.raises(AuthorityDenied):
        runtime.operator.command(operator_ctx, command_type="region_shutdown", target_id="AU", reason="test", high_risk=True)

    command = runtime.operator.command(
        operator_ctx,
        command_type="region_shutdown",
        target_id="AU",
        reason="test",
        high_risk=True,
        approval_reference="approval-four-eyes",
    )
    assert command.authority_decision == "APPROVED"
