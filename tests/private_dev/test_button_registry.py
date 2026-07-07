from __future__ import annotations

import pytest

from tests.private_dev._helpers import assert_contains_all, read_json, read_text


pytestmark = [pytest.mark.private_dev, pytest.mark.local_only]


def test_private_dev_button_registry_matches_app_sources() -> None:
    registry = read_json("docs/mobile/private_dev_button_registry.json")
    assert "apps" in registry

    for app_name, spec in registry["apps"].items():
        source = read_text(spec["source"])
        assert_contains_all(source, list(spec["tabs"]), context=f"{app_name} tabs")
        assert_contains_all(source, list(spec["buttons"]), context=f"{app_name} buttons")
        assert "TODO" not in source
        assert "console.log(" not in source

