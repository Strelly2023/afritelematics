from __future__ import annotations

import json
from pathlib import Path

from afritech.afriprogramming.rbac import role_definition


FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures/novacodepro_role_accounts.json"


def test_novacodepro_role_accounts_fixture_is_consistent() -> None:
    payload = json.loads(FIXTURE_PATH.read_text())

    accounts = payload["accounts"]
    super_account = payload["super_test_account"]

    assert payload["shared_credentials"]["status"] == "ACTIVE"
    assert len(accounts) == 25
    assert len({account["email"] for account in accounts}) == len(accounts)
    assert len({account["username"] for account in accounts}) == len(accounts)
    assert {account["role"] for account in accounts} == {
        "ADMIN",
        "DEVELOPER",
        "PRODUCT_MANAGER",
        "BUSINESS_ANALYST",
        "UI_UX_DESIGNER",
        "PROJECT_MANAGER",
        "ARCHITECT",
        "QA_ENGINEER",
        "DEVOPS_ENGINEER",
        "CUSTOMER_SUPPORT",
        "OPERATIONS_TEAM",
        "BRAND_TEAM",
        "COMPLIANCE_TEAM",
        "AUDIT_TEAM",
        "SECURITY_ENGINEER",
        "INCIDENT_RESPONSE_TEAM",
        "DATA_ARCHITECT",
        "DATA_ENGINEER",
        "DATABASE_ENGINEER",
        "AI_ML_ENGINEER",
        "DATA_SCIENTIST",
        "PRIVACY_COMPLIANCE",
        "RISK_MANAGEMENT",
        "LEGAL",
        "EXTERNAL_REGULATOR",
    }
    assert all(role_definition(account["role"]) for account in accounts)
    assert super_account["username"] == "djuma"
    assert super_account["email"] == "djstrelly@gmail.com"
    assert set(super_account["assigned_roles"]) == {account["role"] for account in accounts}
