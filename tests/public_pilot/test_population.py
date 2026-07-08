from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_APPROVED_LOCATIONS, PUBLIC_PILOT_PARTICIPANTS, public_pilot_population_payload, read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_guard]


def test_public_pilot_population_summary_matches_completion_profile() -> None:
    payload = public_pilot_population_payload()
    assert payload["total_participants"] == 57
    assert len(payload["devices"]) == 40
    assert len(payload["groups"]["drivers"]) == 10
    assert len(payload["groups"]["riders"]) == 30
    assert len(payload["groups"]["merchants"]) == 2
    assert len(payload["groups"]["agents"]) == 3
    assert len(payload["groups"]["businesses"]) == 2
    assert len(payload["groups"]["employees"]) == 10

    text = read_text("docs/public_pilot/PUBLIC_PILOT_POPULATION.md")
    for phrase in ("57", "40 trusted devices", "READY_FOR_PRR", "PUBLIC_PILOT"):
        assert phrase.lower() in text.lower()


def test_public_pilot_population_participant_groups_do_not_overlap() -> None:
    groups = list(PUBLIC_PILOT_PARTICIPANTS.values())
    flattened = [participant for group in groups for participant in group]
    assert len(flattened) == len(set(flattened))


def test_public_pilot_approved_locations_are_documented() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_LOCATIONS.md")
    for location in PUBLIC_PILOT_APPROVED_LOCATIONS:
        assert location in text
