from __future__ import annotations

import pytest

from tests.internal_qa._helpers import BUTTON_REGISTRY_PATH, read_json, read_text
from tests.private_dev._helpers import assert_contains_all


pytestmark = [
    pytest.mark.internal_qa,
    pytest.mark.qa_mobile,
    pytest.mark.novaid,
    pytest.mark.identity,
]


def test_novaid_internal_qa_app_surfaces_are_documented() -> None:
    registry = read_json(BUTTON_REGISTRY_PATH)["apps"]
    personal = read_text("novaid_personal_app/src/appConfig.ts")
    business = read_text("novaid_business_app/src/appConfig.ts")
    employee = read_text("novaid_employee_app/src/appConfig.ts")
    partner = read_text("novaid_partner_app/src/appConfig.ts")
    inspector = read_text("novaid_inspector_app/src/appConfig.ts")

    assert_contains_all(personal, registry["novaid_personal"]["tabs"], context="NovaID personal tabs")
    assert_contains_all(personal, registry["novaid_personal"]["buttons"], context="NovaID personal buttons")
    assert_contains_all(business, registry["novaid_business"]["tabs"], context="NovaID business tabs")
    assert_contains_all(business, registry["novaid_business"]["buttons"], context="NovaID business buttons")
    assert_contains_all(employee, registry["novaid_employee"]["tabs"], context="NovaID employee tabs")
    assert_contains_all(employee, registry["novaid_employee"]["buttons"], context="NovaID employee buttons")
    assert_contains_all(partner, registry["novaid_partner"]["tabs"], context="NovaID partner tabs")
    assert_contains_all(partner, registry["novaid_partner"]["buttons"], context="NovaID partner buttons")
    assert_contains_all(inspector, registry["novaid_inspector"]["tabs"], context="NovaID inspector tabs")
    assert_contains_all(inspector, registry["novaid_inspector"]["buttons"], context="NovaID inspector buttons")
