from __future__ import annotations

import pytest

from tests.internal_qa._helpers import BUTTON_REGISTRY_PATH, read_json, read_text
from tests.private_dev._helpers import assert_contains_all


pytestmark = [pytest.mark.internal_qa, pytest.mark.qa_button_registry]


def test_internal_qa_button_registry_matches_app_sources() -> None:
    registry = read_json(BUTTON_REGISTRY_PATH)["apps"]
    for app_name, app_registry in registry.items():
        source = read_text(app_registry["source"])
        assert_contains_all(source, app_registry["tabs"], context=f"{app_name} tabs")
        assert_contains_all(source, app_registry["buttons"], context=f"{app_name} buttons")
        assert "TODO" not in source
        assert "console.log(" not in source
