from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_driver_app_is_locked_to_test_build_profile() -> None:
    app = read("App.tsx")
    app_config = read("app.json")
    eas = read("eas.json")

    assert "AfriRide Driver (Test)" in app_config
    assert "afriride-driver-test" in app_config
    assert '"test_mode": true' in app_config
    assert '"distribution": "internal"' in eas
    assert '"buildType": "apk"' in eas
    assert "EXPO_PUBLIC_AFRIRIDE_TEST_MODE" in eas
    assert "if (!TEST_MODE)" in app
    assert 'throw new Error("Test mode required")' in app


def test_driver_api_layer_owns_required_http_paths() -> None:
    source = read("core/api/driver.service.ts")
    evidence = read("core/services/pilotEvidence.service.ts")

    assert "USE_MOCK_API" in source
    assert '"/driver/availability"' in source
    assert "`/driver/${encodeURIComponent(driverId)}/queue`" in source
    assert "`/ride/${rideId}/accept`" in source
    assert "`/ride/${rideId}/reject`" in source
    assert '"/ride/arrive"' in source
    assert "`/ride/${rideId}/start`" in source
    assert "`/ride/${rideId}/complete`" in source
    assert "`/driver/${encodeURIComponent(driverId)}/earnings`" in source
    assert "`/driver/replay-history?driver_id=${encodeURIComponent(driverId)}`" in source
    assert "/pilot/evidence" in evidence


def test_driver_api_client_sends_test_instrumentation() -> None:
    source = read("core/api/client.ts")
    instrumentation = read("core/api/testInstrumentation.ts")
    environment = read("core/config/environment.ts")

    assert "buildClientEvent({" in source
    assert "path," in source
    assert "method," in source
    assert "payload: options.body" in source
    assert "instrumentationHeaders(clientEvent)" in source
    assert "withClientEvent(options.body, clientEvent)" in source
    assert '"network_latency_event"' in source
    assert '"X-AfriRide-Device-Id"' in instrumentation
    assert '"X-AfriRide-Event-Id"' in instrumentation
    assert "client_event" in instrumentation
    assert 'actor_type: "driver"' in instrumentation
    assert "actor_id" in instrumentation
    assert "action:" in instrumentation
    assert "local_timestamp" in instrumentation
    assert "payload:" in instrumentation
    assert "TEST_MODE" in environment
    assert "DEVICE_ID" in environment


def test_availability_screen_only_requests_state_changes() -> None:
    source = read("ui/screens/AvailabilityScreen.tsx")

    assert "onGoAvailable" in source
    assert "onGoOffline" in source
    assert "Go available" in source


def test_driver_app_exposes_pilot_diagnostics_and_real_world_evidence() -> None:
    app = read("App.tsx")
    diagnostics = read("ui/screens/DiagnosticsScreen.tsx")
    pilot_hook = read("state/providers/usePilotEvidence.ts")
    evidence_service = read("core/services/pilotEvidence.service.ts")
    models = read("core/models/pilotEvidence.ts")

    assert "DiagnosticsScreen" in app
    assert "usePilotEvidence" in app
    assert "Start evidence shift" in diagnostics
    assert "driver_shift_started" in pilot_hook
    assert "driver_location_event" in pilot_hook
    assert "gps_accuracy_event" in evidence_service
    assert "route_deviation_event" in evidence_service
    assert "speed_consistency_event" in evidence_service
    assert "gps_signal_loss_event" in pilot_hook
    assert "routeDeviationEvents" in diagnostics
    assert "gpsSignalLossEvents" in diagnostics
    assert "describePilotEvidenceError" in pilot_hook
    assert "extractPilotEvidenceError" in pilot_hook
    assert "if (!diagnostics.shiftStarted)" in pilot_hook
    assert "lastEvidenceError" in pilot_hook
    assert 'type: "timeout" | "network" | "validation" | "shift_gated" | "server" | "unknown"' in models
    assert 'severity: EvidenceErrorSeverity' in models
    assert "durationMs: number" in models
    assert "traceId: string" in models
    assert "evidence_api_timeout" in evidence_service
    assert "API_BASE_URL" in evidence_service
    assert "buildEvidenceError" in evidence_service
    assert "generateEvidenceTraceContext" in evidence_service
    assert '"X-AfriRide-Trace-Id"' in evidence_service
    assert "traceparent" in evidence_service
    assert "`00-${traceId}-${spanId}-01`" in evidence_service
    assert "app_backgrounded" in pilot_hook
    assert "app_resumed" in pilot_hook
    assert "crash_event" in app
    assert "ride_accept_latency" in models


def test_ride_requests_screen_exposes_accept_and_reject_only() -> None:
    source = read("ui/screens/RideRequestsScreen.tsx")

    assert "onAccept" in source
    assert "onReject" in source
    assert "quotedTotalText" in source


def test_trip_lifecycle_screen_requires_system_state() -> None:
    source = read("ui/screens/TripLifecycleScreen.tsx")

    assert "assertTripSnapshot(trip)" in source
    assert "onArrived" in source
    assert "onStart" in source
    assert "onComplete" in source


def test_earnings_screen_requires_core_source() -> None:
    source = read("ui/screens/EarningsScreen.tsx")

    assert "assertEarningsEvidence(earnings)" in source
    assert "earnings.source" in source
    assert "earnings.totalText" in source


def test_replay_history_screen_requires_replay_evidence() -> None:
    source = read("ui/screens/ReplayHistoryScreen.tsx")

    assert "assertReplayHistory(replayHistory)" in source
    assert "item.replayId" in source
    assert "item.replayVerified" in source


def test_mock_api_stays_inside_driver_api_layer() -> None:
    source = read("core/api/mockDriver.service.ts")

    assert "source: \"core_system\"" in source
    assert "replayVerified: true" in source
    assert "MOCK_RIDE_ID" in source
