from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_APPROVED_LOCATIONS, read_json, read_text


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_access_control]


def test_public_pilot_locations_registry_exists_and_is_pilot_enabled() -> None:
    locations = read_json("pilot/public_pilot/pilot_locations.json")
    assert len(locations) == len(PUBLIC_PILOT_APPROVED_LOCATIONS)
    assert [location["city"] for location in locations] == PUBLIC_PILOT_APPROVED_LOCATIONS
    assert all(location["pilot_enabled"] is True for location in locations)
    assert all(location["service_radius_km"] > 0 for location in locations)


def test_public_pilot_locations_document_mentions_restricted_geography() -> None:
    text = read_text("docs/public_pilot/PUBLIC_PILOT_LOCATIONS.md")
    for phrase in ("pilot restricted", "location monitoring", "approved pilot locations"):
        assert phrase in text.lower()
