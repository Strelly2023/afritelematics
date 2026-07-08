from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import read_text


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_release_guard]


def test_controlled_pilot_exit_criteria_include_formal_definition() -> None:
    doc = read_text("docs/pilot/CONTROLLED_PILOT_EXIT_CRITERIA.md")
    for phrase in [
        "Goal is to validate core workflows, security controls, RBAC, device trust, identity verification, payment flows, audit logs, and support processes.",
        "internal staff, trusted partners, selected drivers, selected merchants, test consumers, operations team",
        "approved users only, approved drivers only, approved merchants only, approved devices only, restricted access lists, simulated or tightly controlled payments, internal operational oversight, limited test geography, high-touch support",
        "controlled-pilot tests passing, safety controls verified, no critical defects, governance approval granted",
    ]:
        assert phrase in doc

    assert "General availability remains false unless explicitly approved." in doc
    assert "Any live payment path is active without approval." in doc

