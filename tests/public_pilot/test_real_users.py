from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_PARTICIPANTS, read_json, read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.approved_users_only]


def test_public_pilot_user_registries_are_non_overlapping() -> None:
    approved_users = read_json("docs/public_pilot/PUBLIC_PILOT_APPROVAL.json")["approved_users"]
    assert len(approved_users) == 57

    registries = {
        "drivers": read_json("pilot/public_pilot/approved_drivers.json"),
        "riders": read_json("pilot/public_pilot/approved_riders.json"),
        "merchants": read_json("pilot/public_pilot/approved_merchants.json"),
        "agents": read_json("pilot/public_pilot/approved_agents.json"),
        "businesses": read_json("pilot/public_pilot/approved_businesses.json"),
        "employees": read_json("pilot/public_pilot/approved_employees.json"),
    }
    flattened = []
    for registry in registries.values():
        flattened.extend(entry["user_id"] for entry in registry)
    assert len(flattened) == 57
    assert len(flattened) == len(set(flattened))
    assert set(flattened) == set(approved_users)
    assert all(len(registry) == len(PUBLIC_PILOT_PARTICIPANTS[name]) for name, registry in registries.items())


def test_public_pilot_users_document_describes_invitation_based_public_pilot() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_USERS.md")
    for phrase in (
        "invitation-based",
        "real riders",
        "real drivers",
        "real merchants",
        "real agents",
        "real businesses",
        "real employees",
    ):
        assert phrase in text.lower()
