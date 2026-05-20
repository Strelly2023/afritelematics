"""Value object helpers for ride requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GeoPoint:
    lat: float
    lng: float

    def as_payload(self) -> dict[str, float]:
        return {"lat": self.lat, "lng": self.lng}
