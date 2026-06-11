from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
DOC = ROOT / "docs/mobile/AFRIRIDE_MOBILE_PLATFORM_READINESS.md"


def test_mobile_platform_readiness_doc_preserves_cross_platform_boundary() -> None:
    text = DOC.read_text(encoding="utf-8")

    for item in (
        "MOBILE PLATFORM READINESS",
        "CROSS_PLATFORM_MOBILE_EXECUTION_SURFACE",
        "Expo / React Native execution apps",
        "Flutter pilot clients",
        "expo start --android",
        "expo start --ios",
        "Android + iOS cross-platform clients",
        "Android scaffolding visible in the repo",
    ):
        assert item in text


def test_mobile_platform_readiness_doc_requires_real_device_checks() -> None:
    text = DOC.read_text(encoding="utf-8")

    for item in (
        "Technical Checklist Before First Partner Demo",
        "Permissions",
        "Time And Trace Discipline",
        "Offline / Weak Network Handling",
        "idempotency key reuse safety",
        "delayed request retry behavior",
        "local clock normalization assumptions",
    ):
        assert item in text


def test_mobile_platform_readiness_doc_blocks_overclaiming() -> None:
    text = DOC.read_text(encoding="utf-8")

    for item in (
        "all mobile surfaces are already app-store-ready on both Android and iOS",
        "all mobile clients are already published to the App Store and Play Store",
    ):
        assert item in text
