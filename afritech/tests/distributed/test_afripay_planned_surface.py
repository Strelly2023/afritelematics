from __future__ import annotations

from afritech.ci.afripay_planned_surface_validator import DOC, ROOT, validate


def test_afripay_planned_surface_validator_passes():
    assert validate() is True


def test_afripay_core_is_implemented_but_live_settlement_is_gated():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "AfriPay GA Elite Implementation Surface" in text
    assert "Implementation: ACTIVE CORE" in text
    assert "Live Settlement: FORBIDDEN BY DEFAULT" in text
    assert "Provider Mode: deterministic adapter unless compliance activation is explicit" in text
    assert "No transaction means no AfriPay." in text


def test_afripay_implementation_declares_financial_invariants():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "double-entry ledger" in text
    assert "adaptive multi-rail routing" in text
    assert "No live-money movement may occur from deterministic adapters." in text
    assert "Provider callbacks never define ledger truth." in text
    assert "Payment references must be idempotent." in text
