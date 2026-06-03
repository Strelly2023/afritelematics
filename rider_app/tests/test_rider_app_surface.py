from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_booking_screen_submits_request_through_prop() -> None:
    source = read("ui/screens/BookingScreen.tsx")

    assert "onRequestRide" in source
    assert "Request ride" in source


def test_rider_app_is_locked_to_test_build_profile() -> None:
    app = read("App.tsx")
    app_config = read("app.json")
    eas = read("eas.json")

    assert "AfriRide Rider (Test)" in app_config
    assert "afriride-rider-test" in app_config
    assert '"test_mode": true' in app_config
    assert '"distribution": "internal"' in eas
    assert '"buildType": "apk"' in eas
    assert "EXPO_PUBLIC_AFRIRIDE_TEST_MODE" in eas
    assert "if (!TEST_MODE)" in app
    assert 'throw new Error("Test mode required")' in app


def test_ride_service_maps_required_contract_endpoints() -> None:
    source = read("core/api/ride.service.ts")

    assert "USE_MOCK_API" in source
    assert '"/ride/request"' in source
    assert "`/ride/${rideId}/status`" in source
    assert "`/ride/${rideId}/receipt`" in source
    assert "`/ride/${rideId}/replay`" in source
    assert "`/ride/${rideId}/ledger-receipt`" in source
    assert "`/ride/${rideId}/price-explanation`" in source


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
