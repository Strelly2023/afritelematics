from __future__ import annotations

import sys

from ecosystems.afriride.client.device_model import MobileEvent
from ecosystems.afriride.client.replay_engine import ClientReplayEngine, hash_client_trace


def run() -> None:
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
