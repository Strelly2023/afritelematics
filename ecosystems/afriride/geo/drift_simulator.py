from __future__ import annotations

import random

from ecosystems.afriride.geo.types import GeoPoint


class DriftSimulator:
    def __init__(self, max_delta: float = 0.0001) -> None:
        self.max_delta = max_delta

    def apply_drift(self, point: GeoPoint, *, seed: int) -> GeoPoint:
        rng = random.Random(f"{int(seed)}:{point.timestamp}")
        noise_lat = rng.uniform(-self.max_delta, self.max_delta)
        noise_lon = rng.uniform(-self.max_delta, self.max_delta)
        return GeoPoint(
            lat=round(point.lat + noise_lat, 7),
            lon=round(point.lon + noise_lon, 7),
            timestamp=point.timestamp,
        )
