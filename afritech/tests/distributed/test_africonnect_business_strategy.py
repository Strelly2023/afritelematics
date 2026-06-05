from __future__ import annotations

from pathlib import Path

from afritech.ci.africonnect_business_strategy_validator import DOC, ROOT, validate


def test_africonnect_business_strategy_validator_passes():
    assert validate() is True


def test_africonnect_business_strategy_keeps_dual_structure_and_claim_discipline():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "Business layer: AfriConnect Transport, Logistics & Warehouse" in text
    assert "Technology layer: AfriTech and AfriConnectTL" in text
    assert "building verifiable delivery capability" in text
    assert "not as a fully proven autonomous logistics network" in text
    assert "protocol-backed claims require evidence bundles" in text


def test_africonnect_business_strategy_lives_in_operations_docs():
    path = ROOT / DOC

    assert path == Path(ROOT / "docs/operations/AFRICONNECT_LOGISTICS_BUSINESS_STRATEGY.md")
    assert path.exists()
