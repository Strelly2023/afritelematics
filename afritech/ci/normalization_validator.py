from __future__ import annotations

import sys

from afritech.edge.ingestion.reality_ingestor import admit_normalized_reality_events
from afritech.edge.normalization.reality_events import normalize_reality_events
from afritech.simulation.validation_receipt import build_validation_receipt, stable_hash
#afritech.ci.normalization_validator

def build_receipt():
    observations = [
        {
            "source_id": "device-a",
            "event_id": "evt-002",
            "event_kind": "driver_location",
            "observed_at_ms": 1_700_000_900_999,
            "received_at_ms": 1_700_000_002_111,
            "payload": {
                "trip_id": "trip-1",
                "latitude": "-37.813628",
                "longitude": "144.963058",
            },
        },
        {
            "source_id": "device-a",
            "event_id": "evt-001",
            "event_kind": "ride_request",
            "observed_at_ms": 1_699_999_999_999,
            "received_at_ms": 1_700_000_001_999,
            "payload": {"city_id": "melbourne", "destination": "airport"},
        },
        {
            "source_id": "device-a",
            "event_id": "evt-002",
            "event_kind": "driver_location",
            "observed_at_ms": 1_700_000_900_999,
            "received_at_ms": 1_700_000_002_111,
            "payload": {
                "longitude": "144.963058",
                "latitude": "-37.813628",
                "trip_id": "trip-1",
            },
        },
    ]

    trace_a = normalize_reality_events(
        observations,
        source_adapter_version="mobile-gps-v1",
    )
    trace_b = normalize_reality_events(
        reversed(observations),
        source_adapter_version="mobile-gps-v1",
    )
    if trace_a != trace_b:
        raise RuntimeError("Reality normalization trace is order-dependent")
    if len(trace_a) != 2:
        raise RuntimeError("Reality normalization did not collapse duplicate input")

    admitted_trace = admit_normalized_reality_events(trace_a)
    if admitted_trace[0]["trace"]["stages"] != [
        "adapter",
        "normalization",
        "ingestion",
    ]:
        raise RuntimeError("Reality normalization did not preserve ingestion trace")

    _assert_rejects_authority_injection()
    _assert_rejects_conflicting_duplicate()
    _assert_rejects_tampered_normalized_event(trace_a)

    return build_validation_receipt(
        surface="afritech.edge.normalization.reality_events",
        validator="afritech.ci.normalization_validator",
        inputs=observations,
        outputs={
            "admitted_trace_hash": stable_hash(admitted_trace),
            "admitted_event_count": len(admitted_trace),
        },
        trace=admitted_trace,
        evidence=(
            "normalized_event_trace",
            "normalized_event_admission_trace",
            "clock_drift_normalization_receipt",
            "duplicate_delivery_rejection_trace",
            "replay_injection_rejection_trace",
            "tampered_normalized_event_rejection_trace",
        ),
    )


def _assert_rejects_authority_injection() -> None:
    injected = [
        {
            "source_id": "device-a",
            "event_id": "evt-injected",
            "received_at_ms": 1_700_000_003_000,
            "payload": {"replay_hash": "attacker-controlled"},
        }
    ]
    try:
        normalize_reality_events(injected, source_adapter_version="mobile-v1")
    except ValueError:
        return
    raise RuntimeError("Reality normalization admitted replay authority injection")


def _assert_rejects_conflicting_duplicate() -> None:
    duplicate = [
        {
            "source_id": "device-a",
            "event_id": "evt-dup",
            "received_at_ms": 1_700_000_003_000,
            "payload": {"destination": "airport"},
        },
        {
            "source_id": "device-a",
            "event_id": "evt-dup",
            "received_at_ms": 1_700_000_003_000,
            "payload": {"destination": "cbd"},
        },
    ]
    try:
        normalize_reality_events(duplicate, source_adapter_version="mobile-v1")
    except ValueError:
        return
    raise RuntimeError("Reality normalization admitted conflicting duplicate input")


def _assert_rejects_tampered_normalized_event(trace) -> None:
    tampered = list(trace)
    tampered[0] = {**tampered[0], "normalized_event_id": "0" * 64}
    try:
        admit_normalized_reality_events(tampered)
    except ValueError:
        return
    raise RuntimeError("Reality admission admitted tampered normalized event")


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Normalization validation receipt is not replay safe")
    print("Reality normalization validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"Reality normalization validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
