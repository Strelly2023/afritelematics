from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_driver_app_has_pilot_and_store_build_profiles() -> None:
    app = read("App.tsx")
    app_config = read("app.json")
    eas = read("eas.json")

    assert "AfriRide Driver (Test)" in app_config
    assert "afriride-driver-test" in app_config
    assert '"test_mode": true' in app_config
    assert '"distribution": "internal"' in eas
    assert '"distribution": "store"' in eas
    assert '"buildType": "apk"' in eas
    assert '"pilot-ios"' in eas
    assert '"owner": "ostrinov23"' in app_config
    assert "ITSAppUsesNonExemptEncryption" in app_config
    assert "EXPO_PUBLIC_AFRIRIDE_TEST_MODE" in eas
    assert "TEST_MODE ? \"Pilot\" : \"Live\"" in app
    assert 'throw new Error("Test mode required")' not in app


def test_driver_api_layer_owns_required_http_paths() -> None:
    source = read("core/api/driver.service.ts")
    evidence = read("core/services/pilotEvidence.service.ts")

    assert "USE_MOCK_API" in source
    assert "/v1/driver/${encodeURIComponent(driverId)}/availability" in source
    assert "/v1/driver/${encodeURIComponent(driverId)}/ride-queue" in source
    assert "/v1/driver/rides/${encodeURIComponent(rideId)}/accept" in source
    assert "/v1/driver/rides/${encodeURIComponent(rideId)}/reject" in source
    assert "/v1/driver/rides/${encodeURIComponent(rideId)}/arrive" in source
    assert "/v1/driver/rides/${encodeURIComponent(rideId)}/start" in source
    assert "/v1/driver/rides/${encodeURIComponent(rideId)}/complete" in source
    assert "/v1/driver/${encodeURIComponent(driverId)}/earnings" in source
    assert "/v1/driver/${encodeURIComponent(driverId)}/replay-history" in source
    assert "trust_score" in source
    assert "replay_verified" in source
    assert "/pilot/evidence" in evidence


def test_operator_dashboard_exposes_fleet_trust_surfaces() -> None:
    app = read("App.tsx")
    screen = read("ui/screens/OperatorDashboardScreen.tsx")
    service = read("core/api/operator.service.ts")
    mock = read("core/api/mockOperator.service.ts")

    assert "OperatorDashboardScreen" in app
    assert "useOperatorDashboard" in app
    assert "Fleet Trust" in screen
    assert "Pilot Evidence" in screen
    assert "Replay Exceptions" in screen
    assert "Driver Trust Trends" in screen
    assert "Public Verification Status" in screen
    assert '"/v1/operator/dashboard"' in service
    assert "USE_MOCK_API" in service
    assert "fleetTrustScore" in mock
    assert "publicVerification" in mock


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


def test_novaride_driver_trust_uix_primitives_are_integrated() -> None:
    widgets = [
        "TrustScoreCard",
        "LifecycleTimeline",
        "HumanReceiptCard",
        "VerificationStatusCard",
        "MapPreviewCard",
        "PaymentVerificationCard",
        "EvidenceSummaryCard",
        "DriverReputationCard",
    ]

    for widget in widgets:
        source = read(f"ui/widgets/{widget}.tsx")
        assert f"function {widget}" in source

    lifecycle = read("ui/screens/TripLifecycleScreen.tsx")
    earnings = read("ui/screens/EarningsScreen.tsx")
    trust_profile = read("ui/screens/DriverTrustProfileScreen.tsx")
    tokens = read("ui/theme/trustTokens.ts")

    assert "trustLevelColor" in tokens
    assert "TrustScoreCard" in lifecycle
    assert "MapPreviewCard" in lifecycle
    assert "LifecycleTimeline" in lifecycle
    assert "PaymentVerificationCard" in lifecycle
    assert "EvidenceSummaryCard" in lifecycle
    assert "TrustScoreCard" in earnings
    assert "PaymentVerificationCard" in earnings
    assert "DriverReputationCard" in earnings
    assert "TrustScoreCard" in trust_profile
    assert "DriverReputationCard" in trust_profile
    assert "EvidenceSummaryCard" in trust_profile


def test_driver_product_completion_surfaces_are_wired() -> None:
    app = read("App.tsx")
    screens = [
        "DriverLoginScreen",
        "DriverProfileScreen",
        "VehicleManagementScreen",
        "DriverNotificationsScreen",
    ]

    for screen in screens:
        source = read(f"ui/screens/{screen}.tsx")
        assert f"function {screen}" in source
        assert screen in app

    tabs = read("ui/widgets/ProductTabs.tsx")

    assert "ProductTabs" in app
    assert '"control"' in app
    assert '"trips"' in app
    assert '"trust"' in app
    assert '"profile"' in app
    assert '"alerts"' in app
    assert "setAuthenticated(true)" in app
    assert "availability?.status" in app
    assert "accessibilityRole=\"button\"" in tabs


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
