from __future__ import annotations

import pytest

from tests.controlled_pilot._helpers import BUTTON_REGISTRY_PATH, assert_contains_all, load_source_text, read_json


pytestmark = [pytest.mark.controlled_pilot, pytest.mark.pilot_mobile, pytest.mark.pilot_release_guard, pytest.mark.pilot_api, pytest.mark.pilot_smoke, pytest.mark.qa_button_registry]


def test_controlled_pilot_button_registry_matches_app_surfaces() -> None:
    registry = read_json("docs/mobile/controlled_pilot_button_registry.json")
    apps = registry["apps"]
    assert registry["environment"] == "CONTROLLED_PILOT"
    assert registry["pilot_controlled"] is True

    for app_key, spec in apps.items():
        source = load_source_text(app_key)
        assert spec["pilot_controlled"] is True
        assert_contains_all(source, spec["tabs"], context=f"{app_key} tabs")
        assert_contains_all(source, spec["buttons"], context=f"{app_key} buttons")
        assert any(marker in source for marker in ("onPress", "Pressable", "navigate", "route", "handler"))
        assert "console.log(" not in source
        if any(label for label in spec["buttons"] if any(term in label.lower() for term in ("delete", "remove", "suspend", "reject", "cancel", "revoke", "freeze", "dispute"))):
            assert "confirm" in source.lower() or "review" in source.lower() or "approval" in source.lower()


def test_button_registry_is_controlled_pilot_only() -> None:
    source = read_json("docs/mobile/controlled_pilot_button_registry.json")
    assert source["environment"] == "CONTROLLED_PILOT"
    assert source["pilot_controlled"] is True
