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
    assert "result.ledger_proof?.event_count ?? result.event_count" in source
    assert "result.signature_validation?.signature_mode" in source
    assert "result.identity_validation?.all_verified" in source


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

    assert "isLedgerReceiptUsable(ledgerReceipt)" in source
    assert "Trip receipt is verified. Portable proof is still syncing" in source
    assert "receipt.receiptId" in source
    assert "ledgerReceipt.receiptHash" in source
    assert 'receipt.status === "completed"' in source


def test_replay_screen_requires_verified_evidence() -> None:
    source = read("ui/screens/ReplayScreen.tsx")

    assert "const replayReady" in source
    assert "const replayVerified" in source
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


def test_rider_app_is_sync_safe_for_partial_evidence() -> None:
    app = read("App.tsx")
    receipt = read("ui/screens/ReceiptScreen.tsx")
    replay = read("ui/screens/ReplayScreen.tsx")
    price = read("ui/screens/PriceExplanationScreen.tsx")
    home = read("ui/screens/RiderHomeScreen.tsx")
    ride_service = read("core/api/ride.service.ts")
    driver_service = read("core/api/driver.service.ts")

    assert "RiderErrorBoundary" in app
    assert "receipt = evidence?.receipt ?? null" in app
    assert "receipt?.status || statusSnapshot?.status" in app
    assert "receipt?: RideReceipt | null" in receipt
    assert "Receipt syncing" in receipt
    assert "replay?: RideReplay | null" in replay
    assert "Replay evidence is syncing" in replay
    assert "Array.isArray(replay.explanationSteps)" in replay
    assert "explanation?: PriceExplanation | null" in price
    assert "const lineItems = Array.isArray(explanation?.lineItems)" in price
    assert "intelligence.trust?.driver_verified" in home
    assert "const intelligenceAlerts = Array.isArray(intelligence?.alerts)" in home
    assert "Array.isArray(result.line_items)" in ride_service
    assert "const rides = Array.isArray(result.rides) ? result.rides : []" in driver_service


def test_wallet_actions_open_add_payment_and_split_fare_flows() -> None:
    source = read("ui/screens/WalletScreen.tsx")

    assert 'setActiveAction("add_payment")' in source
    assert 'setActiveAction("split_fare")' in source
    assert "AddPaymentPanel" in source
    assert "SplitFarePanel" in source
    assert "payment method setup pending" in source
    assert "split request ready" in source


def test_price_explanation_screen_shows_core_source() -> None:
    source = read("ui/screens/PriceExplanationScreen.tsx")

    assert "Price explanation is syncing from the core system." in source
    assert "explanation?.priceExplanation" in source
    assert "explanation?.source" in source


def test_mock_api_stays_inside_api_layer() -> None:
    source = read("core/api/mockRide.service.ts")

    assert "source: \"core_system\"" in source
    assert "replayVerified: true" in source
    assert "receiptId" in source
    assert "ledger-receipt.mock.001" in source


def test_completed_ride_evidence_loader_degrades_optional_proofs() -> None:
    source = read("core/services/rideEvidence.service.ts")

    assert "Promise.allSettled" in source
    assert "fallbackReceipt(rideId)" in source
    assert "fallbackReplay(rideId)" in source
    assert "fallbackLedgerReceipt(rideId)" in source
    assert "fallbackPriceExplanation(rideId)" in source
    assert "REVIEW_REQUIRED" in source
