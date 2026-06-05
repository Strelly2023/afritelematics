from __future__ import annotations

from afritech.ci.afripay_planned_surface_validator import DOC, ROOT, validate


def test_afripay_planned_surface_validator_passes():
    assert validate() is True


def test_afripay_is_conceptual_until_real_transactions_exist():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "AfriPay = Conceptual Financial Surface" in text
    assert "Execution: NONE" in text
    assert "Evidence: NONE" in text
    assert "Activation: FORBIDDEN" in text
    assert "No transaction means no AfriPay." in text


def test_afripay_forbids_financial_implementation_before_evidence():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "no implementation" in text
    assert "no API" in text
    assert "no wallet" in text
    assert "no payment platform claims" in text
    assert "This format is not active yet." in text
