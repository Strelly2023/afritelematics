from __future__ import annotations

from afritech.ci.novapay_mobile_money_validator import validate


def test_novapay_mobile_money_governance_chain_is_complete() -> None:
    report = validate()

    assert report.verified is True
    assert report.governance_chain is True
    assert report.pending_boundary is True
    assert report.callback_security is True
    assert report.trust_receipt is True
