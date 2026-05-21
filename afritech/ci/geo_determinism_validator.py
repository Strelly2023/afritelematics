from __future__ import annotations

import sys

from ecosystems.afriride.geo.engine import GeoEngine, hash_geo_trace
from ecosystems.afriride.geo.types import GeoPoint


def run() -> None:
    start = GeoPoint(lat=-1.2921, lon=36.8219, timestamp=1_700_000_000)
    end = GeoPoint(lat=-1.3032, lon=36.7073, timestamp=1_700_001_200)
    engine = GeoEngine(seed=101)

    trace_a = engine.compute_trip(start, end, steps=12)
    trace_b = engine.compute_trip(start, end, steps=12)

    if trace_a != trace_b:
        raise RuntimeError("Geo trace replay mismatch")
    if hash_geo_trace(trace_a) != hash_geo_trace(trace_b):
        raise RuntimeError("Geo trace hash mismatch")

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
