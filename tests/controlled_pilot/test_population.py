from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import read_json, read_text


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_smoke]


def test_controlled_pilot_population_counts_are_exact_and_non_overlapping() -> None:
    registry = read_json("docs/pilot/approved_pilot_registry.json")
    assert registry["approved_participants_only"] is True
    assert registry["roles_overlap_allowed"] is False
    assert len(registry["approved_users"]) == 57
    assert len(registry["approved_drivers"]) == 10
    assert len(registry["approved_riders"]) == 30
    assert len(registry["approved_merchants"]) == 2
    assert len(registry["approved_agents"]) == 3
    assert len(registry["approved_businesses"]) == 2
    assert len(registry["approved_employees"]) == 10
    assert len(registry["approved_devices"]) == 40

    participants = (
        set(registry["approved_drivers"])
        | set(registry["approved_riders"])
        | set(registry["approved_merchants"])
        | set(registry["approved_agents"])
        | set(registry["approved_businesses"])
        | set(registry["approved_employees"])
    )
    assert len(participants) == 57
    assert len(set(registry["approved_users"])) == 57
    assert set(registry["approved_users"]) == participants


def test_controlled_pilot_population_doc_contains_formal_definition() -> None:
    doc = read_text("docs/pilot/CONTROLLED_PILOT_POPULATION_2026.md")
    for phrase in [
        "Goal is to validate core workflows, security controls, RBAC, device trust, identity verification, payment flows, audit logs, and support processes.",
        "internal staff, trusted partners, selected drivers, selected merchants, test consumers, operations team",
        "approved users only, approved drivers only, approved merchants only, approved devices only, restricted access lists, simulated or tightly controlled payments, internal operational oversight, limited test geography, high-touch support",
        "Does onboarding work?",
        "Do ride flows work?",
        "Do payment flows work?",
        "Does RBAC work?",
        "Do audit logs work?",
        "Are support procedures working?",
        "controlled-pilot tests passing, safety controls verified, no critical defects, governance approval granted",
    ]:
        assert phrase in doc

