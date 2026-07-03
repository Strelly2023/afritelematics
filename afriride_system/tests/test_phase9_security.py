from __future__ import annotations

import hashlib
import hmac
from pathlib import Path

from fastapi.testclient import TestClient

from afriride_system.api.main import app
from afriride_system.api.security import (
    POLICY,
    _consume_rate,
    create_attestation_challenge,
    reset_security_state,
    verify_attestation,
)


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_attestation_challenge_is_device_bound_single_use(monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_ENV", "test")
    monkeypatch.setenv("AFRIRIDE_DEV_ATTESTATION_SECRET", "phase9-secret")
    reset_security_state()
    challenge = create_attestation_challenge("device-9")
    token = hmac.new(
        b"phase9-secret",
        f"android:device-9:{challenge['nonce']}".encode(),
        hashlib.sha256,
    ).hexdigest()
    result = verify_attestation(
        {
            "nonce": challenge["nonce"],
            "device_id": "device-9",
            "platform": "android",
            "token": token,
        }
    )
    assert result["integrity"]["trusted"] is True
    assert result["integrity"]["provider"] == "development_hmac"
    try:
        verify_attestation(
            {
                "nonce": challenge["nonce"],
                "device_id": "device-9",
                "platform": "android",
                "token": token,
            }
        )
    except ValueError as exc:
        assert str(exc) == "attestation_challenge_missing_or_replayed"
    else:
        raise AssertionError("attestation challenge replay accepted")


def test_mutation_nonce_is_rejected_on_replay(monkeypatch) -> None:
    monkeypatch.setenv("AFRIRIDE_ENFORCE_REPLAY_PROTECTION", "true")
    reset_security_state()
    headers = {
        "X-Request-Timestamp": __import__("time").time().__str__(),
        "X-Request-Nonce": "phase9-request-nonce-00000001",
    }
    client = TestClient(app)
    first = client.post("/v1/security/sessions/absent/revoke", headers=headers)
    second = client.post("/v1/security/sessions/absent/revoke", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "REQUEST_REPLAYED"


def test_rate_limiter_returns_retry_after_when_bucket_is_full() -> None:
    reset_security_state()
    now = 1_000.0
    for _ in range(POLICY.anonymous_rate_limit):
        assert _consume_rate("phase9-client", now, POLICY.anonymous_rate_limit) is None
    assert _consume_rate("phase9-client", now, POLICY.anonymous_rate_limit) == 60


def test_mobile_sessions_use_hardware_storage_biometrics_and_request_nonces() -> None:
    shared = read("afriride_system/mobile/shared/secureSession.js")
    assert "expo-secure-store" in shared
    assert "WHEN_UNLOCKED_THIS_DEVICE_ONLY" in shared
    assert "requireAuthentication: true" in shared
    assert "canUseBiometricAuthentication" in shared
    assert '"X-Request-Timestamp"' in shared
    assert '"X-Request-Nonce"' in shared
    for app in ("rider_app", "driver_app"):
        assert "restoreSession" in read(f"{app}/App.tsx")
        assert "attestDevice" in read(f"{app}/core/api/auth.service.ts")


def test_android_and_ios_certificate_pins_are_configured() -> None:
    for app in ("rider_app", "driver_app"):
        manifest = read(f"{app}/android/app/src/main/AndroidManifest.xml")
        network = read(f"{app}/android/app/src/main/res/xml/network_security_config.xml")
        config = read(f"{app}/app.json")
        assert 'android:allowBackup="false"' in manifest
        assert 'android:usesCleartextTraffic="false"' in manifest
        assert 'android:networkSecurityConfig="@xml/network_security_config"' in manifest
        assert "<pin-set" in network
        assert "api.afritechnology.com" in network
        assert "NSPinnedDomains" in config
        assert "SPKI-SHA256-BASE64" in config


def test_android_apps_ship_native_play_integrity_bridge() -> None:
    packages = {
        "rider_app": "com/ostrinov23/afririderapp",
        "driver_app": "com/ostrinov23/afriridedrivertest",
    }
    for app, package in packages.items():
        module = read(
            f"{app}/android/app/src/main/java/{package}/AfriRideIntegrityModule.kt"
        )
        build = read(f"{app}/android/app/build.gradle")
        application = read(f"{app}/android/app/src/main/java/{package}/MainApplication.kt")
        assert "IntegrityManagerFactory.create" in module
        assert "requestIntegrityToken" in module
        assert "response.token()" in module
        assert "com.google.android.play:integrity:1.5.0" in build
        assert "add(AfriRideIntegrityPackage())" in application
