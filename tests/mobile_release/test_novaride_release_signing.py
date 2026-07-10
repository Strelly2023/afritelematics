from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_release_manifest_tracks_signing_fingerprint() -> None:
    for path in [
        ROOT / "docs/mobile/release/novaride_rider_v2026.1.2_manifest.json",
        ROOT / "docs/mobile/release/novaride_driver_v2026.1.2_manifest.json",
        ROOT / "docs/mobile/release/novaride_fleet_v2026.1.2_manifest.json",
        ROOT / "docs/mobile/release/novaride_operator_v2026.1.2_manifest.json",
    ]:
        text = path.read_text(encoding="utf-8")
        assert "signing_certificate_fingerprint" in text
        assert "pending-apksigner" in text or "SHA-256" in text or "sha256" in text.lower()
