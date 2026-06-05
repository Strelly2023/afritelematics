from __future__ import annotations

from afritech.ci.africonnect_burundi_phase1_operations_validator import (
    DOC,
    ROOT,
    validate,
)


def test_africonnect_burundi_phase1_operations_validator_passes():
    assert validate() is True


def test_africonnect_burundi_phase1_keeps_business_before_protocol():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "Phase 1 is business-first and manual by design." in text
    assert "no live protocol claims" in text
    assert "no automatic proof claims" in text
    assert "Business first. Protocol later. Truth after evidence." in text


def test_africonnect_burundi_phase1_has_operational_success_gate():
    text = (ROOT / DOC).read_text(encoding="utf-8")

    assert "10 to 20 deliveries are completed" in text
    assert "all deliveries are recorded" in text
    assert "a consistent manual workflow is established" in text
