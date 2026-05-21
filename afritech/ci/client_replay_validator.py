from __future__ import annotations

import sys

from afritech.simulation.validation_receipt import build_validation_receipt
from ecosystems.afriride.client.device_model import MobileEvent
from ecosystems.afriride.client.replay_engine import ClientReplayEngine, hash_client_trace


def build_receipt():
    events = [
        MobileEvent("device-a", "evt-002", 1_700_001_900, {"action": "start"}),
        MobileEvent("device-a", "evt-001", 1_700_001_100, {"action": "request"}),
        MobileEvent("device-a", "evt-002", 1_700_001_900, {"action": "start"}),
    ]
    engine = ClientReplayEngine()

    trace_a = engine.replay(events)
    trace_b = engine.replay(list(reversed(events)))

    if trace_a != trace_b:
        raise RuntimeError("Client replay mismatch")
    if hash_client_trace(trace_a) != hash_client_trace(trace_b):
        raise RuntimeError("Client replay hash mismatch")
    if len(trace_a) != 2:
        raise RuntimeError("Client replay did not remove duplicate event")

    return build_validation_receipt(
        surface="ecosystems.afriride.client.replay_engine",
        validator="afritech.ci.client_replay_validator",
        inputs=[
            {
                "device_id": event.device_id,
                "event_id": event.event_id,
                "local_timestamp": event.local_timestamp,
                "payload": event.payload,
            }
            for event in events
        ],
        outputs={"client_trace_hash": hash_client_trace(trace_a)},
        trace=trace_a,
        evidence=(
            "client_replay_convergence_trace",
            "duplicate_delivery_rejection_trace",
        ),
    )


def run() -> None:
    receipt = build_receipt()
    if not receipt.deterministic or not receipt.replay_safe:
        raise RuntimeError("Client validation receipt is not replay safe")
    print("✅ Client replay validation PASSED")


def main() -> int:
    try:
        run()
        return 0
    except Exception as exc:
        print(f"❌ Client replay validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
