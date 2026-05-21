from __future__ import annotations

from ecosystems.afriride.geo.types import GeoPoint


class RouteModel:
    """Builds replay-stable route points from recorded start/end inputs."""

    def compute_path(
        self,
        start: GeoPoint,
        end: GeoPoint,
        *,
        seed: int,
        steps: int = 8,
    ) -> tuple[GeoPoint, ...]:
        if steps < 2:
            raise ValueError("steps must be at least 2")

        # Seed is part of the public contract for parity with richer future
        # route models. The current interpolation is intentionally pure.
        _ = int(seed)

        timestamp_delta = end.timestamp - start.timestamp
        points: list[GeoPoint] = []
        for index in range(steps):
            ratio = index / (steps - 1)
            points.append(
                GeoPoint(
                    lat=round(start.lat + (end.lat - start.lat) * ratio, 7),
                    lon=round(start.lon + (end.lon - start.lon) * ratio, 7),
                    timestamp=int(start.timestamp + timestamp_delta * ratio),
                )
            )
        return tuple(points)
