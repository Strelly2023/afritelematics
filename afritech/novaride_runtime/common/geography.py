"""Geography primitives."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GeoPoint:
    lat: float
    lng: float

    def __post_init__(self) -> None:
        if not -90 <= self.lat <= 90:
            raise ValueError("invalid_latitude")
        if not -180 <= self.lng <= 180:
            raise ValueError("invalid_longitude")

    def as_dict(self) -> dict[str, float]:
        return {"lat": self.lat, "lng": self.lng}


@dataclass(frozen=True, slots=True)
class AddressRef:
    label: str
    point: GeoPoint | None = None
    landmark: str | None = None
    airport_terminal: str | None = None
