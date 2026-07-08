from __future__ import annotations

import pytest

from tests.internal_qa._helpers import INTERNAL_QA_CONFIG_PATH, read_json, read_text


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_release_guard]


def test_internal_qa_release_guard_blocks_production_claims() -> None:
    config = read_json(INTERNAL_QA_CONFIG_PATH)
    assert config["environment"] != "PRODUCTION"
    assert config["live_payments_enabled"] is False
    assert config["real_charging_enabled"] is False
    assert config["external_payouts_enabled"] is False
    assert config["production_credentials_allowed"] is False
    assert config["public_launch_allowed"] is False
    assert config["controlled_pilot_allowed"] is False

    manifest_text = "\n".join(
        read_text(path)
        for path in [
            "docs/mobile/release/rider_app_release_manifest.json",
            "docs/mobile/release/driver_app_release_manifest.json",
            "docs/mobile/release/operator_dashboard_release_manifest.json",
            "docs/mobile/release/novapay_consumer_app_release_manifest.json",
            "docs/mobile/release/novapay_agent_app_release_manifest.json",
            "docs/mobile/release/novapay_merchant_app_release_manifest.json",
            "docs/mobile/release/novapay_business_app_release_manifest.json",
            "docs/mobile/release/novaid_personal_app_release_manifest.json",
            "docs/mobile/release/novaid_business_app_release_manifest.json",
            "docs/mobile/release/novaid_employee_app_release_manifest.json",
            "docs/mobile/release/novaid_partner_app_release_manifest.json",
            "docs/mobile/release/novaid_inspector_app_release_manifest.json",
        ]
    ).lower()

    assert "production ready" not in manifest_text
    assert "real payments enabled" not in manifest_text
    assert "debug" not in manifest_text
    assert "live payments" not in manifest_text
