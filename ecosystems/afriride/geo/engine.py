from __future__ import annotations

import hashlib
import json

from ecosystems.afriride.geo.drift_simulator import DriftSimulator
from ecosystems.afriride.geo.route_model import RouteModel
from ecosystems.afriride.geo.traffic_model import TrafficModel
from ecosystems.afriride.geo.types import GeoPoint, GeoTrace


class GeoEngine:
    def __init__(
        self,
        *,
        seed: int,
        route_model: RouteModel | None = None,
        drift_simulator: DriftSimulator | None = None,
        traffic_model: TrafficModel | None = None,
    ) -> None:
        self.seed = int(seed)
        self.route_model = route_model or RouteModel()
        self.drift_simulator = drift_simulator or DriftSimulator()
        self.traffic_model = traffic_model or TrafficModel()

    def compute_trip(
        self,
        start: GeoPoint,
        end: GeoPoint,
        *,
        steps: int = 8,
        base_segment_time: int = 60,
    ) -> GeoTrace:
        route = self.route_model.compute_path(
            start,
            end,
            seed=self.seed,
            steps=steps,
        )
        drifted_route = tuple(
            self.drift_simulator.apply_drift(point, seed=self.seed)
            for point in route
        )
        segment_delays = tuple(
            (
                f"segment-{index}",
                self.traffic_model.delay(
                    f"segment-{index}",
                    base_segment_time,
                    seed=self.seed,
                ),
            )
            for index in range(max(0, len(route) - 1))
        )
        return GeoTrace(
            route=route,
            drifted_route=drifted_route,
            segment_delays=segment_delays,
        )


def hash_geo_trace(trace: GeoTrace) -> str:
    payload = json.dumps(trace.canonical(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()
