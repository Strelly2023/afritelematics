from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_novapay_consumer_branding_and_android_identity() -> None:
    app_config = read("app.json")
    gradle = read("android/app/build.gradle")
    strings = read("android/app/src/main/res/values/strings.xml")
    manifest = read("android/app/src/main/AndroidManifest.xml")
    package = read("package.json")

    assert "NovaPay Consumer (Test)" in app_config
    assert "novapay-consumer-test" in app_config
    assert "com.novatech.novapay.consumer" in app_config
    assert '"CAMERA"' in app_config
    assert "NSCameraUsageDescription" in app_config
    assert "NovaPay Consumer (Test)" in strings
    assert "com.novatech.novapay.consumer" in gradle
    assert "versionCode 4" in gradle
    assert 'versionName "2026.1.0"' in gradle
    assert "com.novatech.novapay.consumer" in manifest
    assert "novapay-consumer-app" in package


def test_consumer_app_shell_exposes_home_wallet_pay_activity_and_profile() -> None:
    app = read("App.tsx")

    assert "NovaPayConsumerApp" in app
    assert 'type TabKey = "home" | "wallet" | "pay" | "activity" | "profile";' in app
    assert '"Home"' in app
    assert '"Wallet"' in app
    assert '"Pay"' in app
    assert '"Activity"' in app
    assert '"Profile"' in app
    assert "Send Money" in app
    assert "Latest receipt" in app
    assert "Security center" in app
    assert "AI assistant" in app
    assert "InteractiveRideMap" not in app
    assert "RiderHomeScreen" not in app


def test_consumer_app_send_flow_and_receipts_are_wired() -> None:
    app = read("App.tsx")

    assert "Recipient, amount, review, authentication, receipt" in app
    assert "NovaPay ID: NP-4839-2026" in app
    assert "Static and dynamic QR payment support" in app
    assert "Transfer completed" in app
    assert "Tamper-evident digital receipt ready to share or download." in app
    assert "receipt replay" in app
    assert "setLatestReceipt" in app
    assert "setFeed((current)" in app


def test_consumer_app_preferences_and_support_sections_are_present() -> None:
    app = read("App.tsx")

    assert "Biometric enabled" in app
    assert "Trusted device" in app
    assert "KYC Level 2" in app
    assert "Language" in app
    assert "Theme" in app
    assert "Large text and high contrast ready" in app
    assert "Live chat" in app
    assert "Ticket tracking" in app
    assert "Call support" in app


def test_novapay_integrity_module_is_rebranded() -> None:
    main_activity = read("android/app/src/main/java/com/ostrinov23/afririderapp/MainActivity.kt")
    main_application = read("android/app/src/main/java/com/ostrinov23/afririderapp/MainApplication.kt")
    integrity_package = read("android/app/src/main/java/com/ostrinov23/afririderapp/AfriRideIntegrityPackage.kt")
    integrity_module = read("android/app/src/main/java/com/ostrinov23/afririderapp/AfriRideIntegrityModule.kt")

    assert "package com.novatech.novapay.consumer" in main_activity
    assert "package com.novatech.novapay.consumer" in main_application
    assert "NovaPayIntegrityPackage" in main_application
    assert "NovaPayIntegrityPackage" in integrity_package
    assert "NovaPayIntegrityModule" in integrity_package
    assert "NovaPayIntegrityModule" in integrity_module
    assert 'override fun getName() = "NovaPayIntegrity"' in integrity_module
