from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_booking_screen_submits_request_through_prop() -> None:
    source = read("ui/screens/BookingScreen.tsx")

    assert "onRequestRide" in source
    assert "Request ride" in source


def test_rider_app_has_pilot_and_store_build_profiles() -> None:
    app = read("App.tsx")
    app_config = read("app.json")
    eas = read("eas.json")

    assert "AfriRide Rider (Test)" in app_config
    assert "afriride-rider-test" in app_config
    assert '"test_mode": true' in app_config
    assert '"distribution": "internal"' in eas
    assert '"distribution": "store"' in eas
    assert '"buildType": "apk"' in eas
    assert '"pilot-ios"' in eas
    assert "NSLocationWhenInUseUsageDescription" in app_config
    assert "ITSAppUsesNonExemptEncryption" in app_config
    assert "EXPO_PUBLIC_AFRIRIDE_TEST_MODE" in eas
    assert "TEST_MODE ? \"Pilot\" : \"Live\"" in app
    assert 'throw new Error("Test mode required")' not in app


def test_ride_service_maps_required_contract_endpoints() -> None:
    source = read("core/api/ride.service.ts")

    assert "USE_MOCK_API" in source
    assert '"/v1/rider/rides"' in source
    assert "/v1/rider/rides/${encodeURIComponent(rideId)}" in source
    assert "/receipt" in source
    assert "/replay" in source
    assert "/ledger-receipt" in source
    assert "/price-explanation" in source
    assert "trust_score" in source
    assert "timeline_events" in source


def test_rider_api_client_sends_test_instrumentation() -> None:
    source = read("core/api/client.ts")
    instrumentation = read("core/api/testInstrumentation.ts")
    environment = read("core/config/environment.ts")

    assert "buildClientEvent({" in source
    assert "path," in source
    assert "method," in source
    assert "payload: options.body" in source
    assert "instrumentationHeaders(clientEvent)" in source
    assert "withClientEvent(options.body, clientEvent)" in source
    assert '"X-AfriRide-Device-Id"' in instrumentation
    assert '"X-AfriRide-Event-Id"' in instrumentation
    assert "client_event" in instrumentation
    assert 'actor_type: "rider"' in instrumentation
    assert "actor_id" in instrumentation
    assert "action:" in instrumentation
    assert "local_timestamp" in instrumentation
    assert "payload:" in instrumentation
    assert "TEST_MODE" in environment
    assert "DEVICE_ID" in environment


def test_receipt_screen_refuses_incomplete_evidence() -> None:
    source = read("ui/screens/ReceiptScreen.tsx")

    assert "assertReceiptEvidence(receipt)" in source
    assert "assertLedgerReceiptEvidence(ledgerReceipt)" in source
    assert "receipt.receiptId" in source
    assert "ledgerReceipt.receiptHash" in source
    assert "receipt.status" not in source


def test_replay_screen_requires_verified_evidence() -> None:
    source = read("ui/screens/ReplayScreen.tsx")

    assert "assertReplayEvidence(replay)" in source
    assert "replay.replayVerified" in source
    assert "replay.explanationSteps" in source


def test_novaride_trust_uix_primitives_are_integrated() -> None:
    widgets = [
        "TrustScoreCard",
        "LifecycleTimeline",
        "HumanReceiptCard",
        "VerificationStatusCard",
        "MapPreviewCard",
        "PaymentVerificationCard",
        "EvidenceSummaryCard",
        "RiderTrustDashboard",
    ]

    for widget in widgets:
        source = read(f"ui/widgets/{widget}.tsx")
        assert f"function {widget}" in source

    live_tracking = read("ui/screens/LiveTrackingScreen.tsx")
    receipt = read("ui/screens/ReceiptScreen.tsx")
    replay = read("ui/screens/ReplayScreen.tsx")
    tokens = read("ui/theme/trustTokens.ts")

    assert "trustLevelColor" in tokens
    assert "TrustScoreCard" in live_tracking
    assert "MapPreviewCard" in live_tracking
    assert "LifecycleTimeline" in live_tracking
    assert "VerificationStatusCard" in live_tracking
    assert "TrustScoreCard" in receipt
    assert "HumanReceiptCard" in receipt
    assert "PaymentVerificationCard" in receipt
    assert "EvidenceSummaryCard" in receipt
    assert "TrustScoreCard" in replay
    assert "LifecycleTimeline" in replay
    assert "EvidenceSummaryCard" in replay


def test_rider_product_completion_surfaces_are_wired() -> None:
    app = read("App.tsx")
    home_source = read("ui/screens/RiderHomeScreen.tsx")
    screens = [
        "RiderLoginScreen",
        "RiderHomeScreen",
        "RiderProfileScreen",
        "RiderNotificationsScreen",
        "WalletScreen",
        "ActivityScreen",
        "EvidenceScreen",
    ]

    for screen in screens:
        source = read(f"ui/screens/{screen}.tsx")
        assert f"function {screen}" in source
        assert screen in app

    tabs = read("ui/widgets/BottomTabs.tsx")
    evidence = read("ui/screens/EvidenceScreen.tsx")

    assert "BottomTabs" in app
    assert '"home"' in app
    assert '"trips"' in app
    assert '"wallet"' in app
    assert '"activity"' in app
    assert '"profile"' in app
    assert "setAuthenticated(true)" in app
    assert "getPassengerIntelligence" in home_source
    assert "System intelligence" in home_source
    assert "Predictive positioning" in home_source
    assert "City-wide AI automation" in home_source
    assert "Multi-city orchestration" in home_source
    assert "ledgerReceipt?.eventCount ?? 0" in evidence
    assert "accessibilityRole=\"button\"" in tabs


def test_price_explanation_screen_shows_core_source() -> None:
    source = read("ui/screens/PriceExplanationScreen.tsx")

    assert "assertPriceEvidence(explanation)" in source
    assert "explanation.priceExplanation" in source
    assert "explanation.source" in source


def test_mock_api_stays_inside_api_layer() -> None:
    source = read("core/api/mockRide.service.ts")

    assert "source: \"core_system\"" in source
    assert "replayVerified: true" in source
    assert "receiptId" in source
    assert "ledger-receipt.mock.001" in source
