from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_driver_runtime_mode_and_realtime_paths_are_explicit() -> None:
    environment = read("core/config/environment.ts")
    runtime_config = read("core/config/runtimeConfig.ts")
    client = read("core/api/client.ts")
    flow = read("state/providers/useDriverFlow.ts")
    realtime = read("../afriride_system/mobile/shared/realtimeClient.ts")

    assert "export type RuntimeMode = \"production\" | \"pilot\" | \"test\";" in environment
    assert "export const RUNTIME_MODE" in environment
    assert "runtimeMode: RUNTIME_MODE" in runtime_config
    assert "assertSecureTransport(API_BASE_URL, TEST_MODE)" in client
    assert "invalid_content_type" in client
    assert "content-type" in client
    assert "AfriRideRealtimeClient" in flow
    assert "USE_MOCK_API" in flow
    assert "mapRealtimeTrip" in flow
    assert "queueDriverOperation" in flow
    assert "reconnectAttempt" in realtime
    assert "cursorKey" in realtime
    assert "sendHeartbeat" in realtime
    assert "scheduleReconnect" in realtime
    assert "HEARTBEAT_MS" in realtime


def test_driver_package_test_gate_runs_full_tree() -> None:
    package_json = read("package.json")
    assert '"test": "npm run typecheck && pytest -q tests"' in package_json
