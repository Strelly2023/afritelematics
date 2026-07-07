from __future__ import annotations

import pytest

from tests.private_dev._helpers import assert_contains_all, read_json, read_text


pytestmark = [pytest.mark.private_dev, pytest.mark.identity]


def test_novaid_personal_business_employee_partner_inspector_surfaces_exist() -> None:
    registry = read_json("docs/mobile/private_dev_button_registry.json")["apps"]

    for app_key in (
        "novaid_personal",
        "novaid_business",
        "novaid_employee",
        "novaid_partner",
        "novaid_inspector",
    ):
        spec = registry[app_key]
        source = read_text(spec["source"])
        assert_contains_all(source, list(spec["tabs"]), context=f"{app_key} tabs")
        assert_contains_all(source, list(spec["buttons"]), context=f"{app_key} buttons")


def test_novaid_private_dev_sandbox_modes_are_documented() -> None:
    personal = read_text("novaid_personal_app/src/appConfig.ts")
    business = read_text("novaid_business_app/src/appConfig.ts")
    employee = read_text("novaid_employee_app/src/appConfig.ts")
    partner = read_text("novaid_partner_app/src/appConfig.ts")
    inspector = read_text("novaid_inspector_app/src/appConfig.ts")

    for source in (personal, business, employee, partner, inspector):
        assert "production" not in source.lower()
        assert "TODO" not in source
        assert "console.log(" not in source
