from __future__ import annotations

import pytest

from tests.public_pilot._helpers import PUBLIC_PILOT_BUTTON_REGISTRY_PATH, assert_contains_all, load_source_text, read_json


pytestmark = [pytest.mark.public_pilot, pytest.mark.public_pilot_guard, pytest.mark.qa_button_registry]


def test_public_pilot_button_registry_matches_app_surfaces() -> None:
    registry = read_json("docs/mobile/public_pilot_button_registry.json")
    assert registry["environment"] == "PUBLIC_PILOT"
    assert registry["ga_enabled"] is False
    assert registry["pilot_geography_restricted"] is True
    assert registry["support_required"] is True
    assert registry["rollback_required"] is True
    for app_key, payload in registry["apps"].items():
        tabs = payload["tabs"]
        buttons = payload["buttons"]
        assert tabs, app_key
        assert buttons, app_key
        assert all("label" in button and "handler" in button for button in buttons)
        assert all(button["handler"].startswith(("identity:", "ride:", "payment:", "support:", "safe:", "proof:", "access:", "fleet:", "wallet:")) for button in buttons)
        assert not any("TODO" in button["handler"] or "console.log" in button["handler"] or "placeholder" in button["handler"] for button in buttons)
        destructive = [button for button in buttons if button["label"] in {"cancel ride", "go offline", "logout", "wallet freeze", "close shift"}]
        assert all(button.get("confirmation_required") is True for button in destructive)


def test_public_pilot_registry_mentions_required_tabs() -> None:
    registry = read_json("docs/mobile/public_pilot_button_registry.json")
    assert "novaride_rider" in registry["apps"]
    assert "novapay_consumer" in registry["apps"]
    assert "novaid_personal" in registry["apps"]
