from __future__ import annotations

import pytest

from afritech.guards.guard_prr import validate as validate_prr_guard
from tests.release._helpers import PRR_PATH, read_text


pytestmark = [pytest.mark.release, pytest.mark.prr]


def test_prr_placeholder_remains_blocked() -> None:
    doc = read_text(PRR_PATH)
    assert "status: BLOCKED" in doc
    assert "certifications_required:" in doc
    assert "engineering_readiness" in doc
    assert "governance approval" in doc.lower() or "governance_approval" in doc.lower()


def test_prr_guard_validates_placeholder_and_config() -> None:
    report = validate_prr_guard()
    assert report["status"] == "PASS"
    assert report["prr_required"] is True
    assert report["prr_blocked"] is True
