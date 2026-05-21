from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, order=True)
class GeoPoint:
    lat: float
    lon: float
    timestamp: int

    def canonical(self) -> dict[str, int | float]:
        return {
            "lat": round(self.lat, 7),
            "lon": round(self.lon, 7),
            "timestamp": int(self.timestamp),
        }


@dataclass(frozen=True)
class GeoTrace:
    route: tuple[GeoPoint, ...]
    drifted_route: tuple[GeoPoint, ...]
    segment_delays: tuple[tuple[str, int], ...]

    def canonical(self) -> dict[str, Any]:
        return {
            "route": [point.canonical() for point in self.route],
            "drifted_route": [point.canonical() for point in self.drifted_route],
            "segment_delays": [
                {"segment_id": segment_id, "delay": delay}
                for segment_id, delay in self.segment_delays
            ],
        }
