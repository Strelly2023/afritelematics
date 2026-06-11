#!/usr/bin/env python3
"""Compare deterministic proof outputs between two AfriRide stores."""

from __future__ import annotations

import argparse
import json

from afriride_system.backend.determinism import (
    collect_ride_snapshot,
    compare_ride_snapshots,
    trace_ride_ids,
)
from afriride_system.backend.storage import AfriRideStorage


def main() -> int:
    args = _parse_args()
    source = AfriRideStorage(args.source)
    target = AfriRideStorage(args.target)

    source_ride_ids = trace_ride_ids(source)
    target_ride_ids = trace_ride_ids(target)
    if source_ride_ids != target_ride_ids:
        print(
            json.dumps(
                {
                    "ok": False,
                    "reason": "ride_id_set_mismatch",
                    "source_ride_ids": list(source_ride_ids),
                    "target_ride_ids": list(target_ride_ids),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 1

    mismatches: dict[str, object] = {}
    for ride_id in source_ride_ids:
        source_snapshot = collect_ride_snapshot(source, ride_id)
        target_snapshot = collect_ride_snapshot(target, ride_id)
        diff = compare_ride_snapshots(source_snapshot, target_snapshot)
        if diff:
            mismatches[ride_id] = diff

    payload = {
        "ok": not mismatches,
        "ride_count": len(source_ride_ids),
        "mismatches": mismatches,
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if not mismatches else 1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="SQLite path or PostgreSQL URL")
    parser.add_argument("--target", required=True, help="SQLite path or PostgreSQL URL")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(main())
