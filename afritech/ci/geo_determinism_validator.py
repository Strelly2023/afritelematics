from __future__ import annotations

import sys

from afritech.simulation.validation_receipt import build_validation_receipt
from ecosystems.afriride.geo.engine import GeoEngine, hash_geo_trace
from ecosystems.afriride.geo.types import GeoPoint


def build_receipt():
    start = GeoPoint(lat=-1.2921, lon=36.8219, timestamp=1_700_000_000)
    end = GeoPoint(lat=-1.3032, lon=36.7073, timestamp=1_700_001_200)
    engine = GeoEngine(seed=101)

    trace_a = engine.compute_trip(start, end, steps=12)
    trace_b = engine.compute_trip(start, end, steps=12)

    if trace_a != trace_b:
        raise RuntimeError("Geo trace replay mismatch")
    if hash_geo_trace(trace_a) != hash_geo_trace(trace_b):
        raise RuntimeError("Geo trace hash mismatch")

    return build_validation_receipt(
        surface="ecosystems.afriride.geo.engine",
        validator="afritech.ci.geo_determinism_validator",
        inputs={
            "start": start.canonical(),
            "end": end.canonical(),
            "seed": 101,
            "steps": 12,
        },
        outputs={"geo_trace_hash": hash_geo_trace(trace_a)},
        trace=trace_a.canonical(),
        evidence=(
            "geo_trace_reconstruction",
            "route_replay_equivalence_hash",
        ),
    )


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Geo validation receipt is not replay safe")
    print("✅ Geo determinism validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Geo determinism validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
