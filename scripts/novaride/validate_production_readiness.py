#!/usr/bin/env python3
"""Validate NovaRide readiness evidence without overstating GA status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("certificate")
    args = parser.parse_args()
    payload = json.loads(Path(args.certificate).read_text())
    if payload.get("final_status") == "READY_FOR_GA":
        required = [
            "live_postgresql_verified",
            "live_kafka_verified",
            "live_kubernetes_failover_verified",
            "emergency_path_verified",
            "security_verified",
            "accessibility_verified",
            "dr_exercise_verified",
        ]
        missing = [key for key in required if payload.get(key) is not True]
        if missing:
            raise SystemExit("ga_status_without_required_evidence:" + ",".join(missing))
    print("novaride_readiness_certificate_valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
