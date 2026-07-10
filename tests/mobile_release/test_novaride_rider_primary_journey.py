from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_rider_booking_journey_is_primary_before_smart_mobility() -> None:
    source = (ROOT / "rider_app/App.tsx").read_text(encoding="utf-8")
    booking_index = source.index("Where are you going?")
    benefits_index = source.index("SMART MOBILITY BENEFITS")
    assert booking_index < benefits_index
    for marker in ["Pickup", "Destination", "CHOOSE RIDE TYPE", "Fare estimate", "Request Ride"]:
        assert marker in source
    assert "Advanced NovaRide capabilities stay here" in source

