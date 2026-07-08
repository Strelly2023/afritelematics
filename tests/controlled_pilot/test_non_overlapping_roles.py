from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_release_guard]


def test_controlled_pilot_roles_do_not_overlap() -> None:
    registry = read_json("docs/pilot/approved_pilot_registry.json")
    group_sets = [
        set(registry["approved_drivers"]),
        set(registry["approved_riders"]),
        set(registry["approved_merchants"]),
        set(registry["approved_agents"]),
        set(registry["approved_businesses"]),
        set(registry["approved_employees"]),
    ]
    for i, left in enumerate(group_sets):
        for right in group_sets[i + 1 :]:
            assert left.isdisjoint(right)
    assert registry["roles_overlap_allowed"] is False

