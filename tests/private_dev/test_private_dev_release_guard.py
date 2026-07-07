from __future__ import annotations

import json

import pytest

from tests.private_dev._helpers import ROOT, read_json, read_text


pytestmark = [pytest.mark.private_dev, pytest.mark.release_guard]


def test_release_guard_blocks_public_launch_and_live_payments() -> None:
    config = read_json("config/private_development.json")
    assert config["environment"] == "PRIVATE_DEVELOPMENT"
    assert config["public_launch_allowed"] is False
    assert config["controlled_pilot_allowed"] is False
    assert config["production_credentials_allowed"] is False
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False


def test_release_manifests_do_not_claim_production_readiness() -> None:
    for manifest_path in (ROOT / "docs/mobile/release").glob("*_release_manifest.json"):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert "production" not in json.dumps(payload).lower()
        assert payload.get("release_channel") != "production"
        assert payload.get("release_channel") != "public_launch"
        assert payload.get("authority_boundary") or payload.get("app_id")


def test_private_dev_docs_exist() -> None:
    for path in [
        "docs/development/PRIVATE_DEVELOPMENT_TEST_PLAN_2026.md",
        "docs/development/PRIVATE_DEVELOPMENT_PAYMENT_BOUNDARIES.md",
        "docs/development/PRIVATE_DEVELOPMENT_APK_TESTING.md",
    ]:
        assert (ROOT / path).is_file(), path

