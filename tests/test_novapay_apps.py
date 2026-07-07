from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]

MOBILE_APPS = {
    "novapay_consumer_app": {
        "package": "com.novatech.novapay.consumer",
        "brand": "NovaPay Consumer",
        "tabs": ["Home", "Pay", "Activity", "Cards", "Profile"],
        "flows": ["Send Money", "Receive Money", "QR Pay"],
    },
    "novapay_agent_app": {
        "package": "com.novatech.novapay.agent",
        "brand": "NovaPay Agent",
        "tabs": ["home", "cash", "scan", "customers", "reports"],
        "flows": ["Cash In", "Cash Out", "Assisted Transfer"],
    },
    "novapay_merchant_app": {
        "package": "com.novatech.novapay.merchant",
        "brand": "NovaPay Merchant",
        "tabs": ["Dashboard", "Collect", "Sales", "Settlements", "More"],
        "flows": ["QR Collections", "POS Payments", "Refunds"],
    },
    "novapay_business_app": {
        "package": "com.novatech.novapay.business",
        "brand": "NovaPay Business",
        "tabs": ["Overview", "Payments", "Approvals", "Reports", "Team"],
        "flows": ["Bulk Payments", "Payroll", "Approvals"],
    },
}

PORTALS = {
    "novapay_operations_portal": ["Live Transactions", "Failed Payments", "System Health"],
    "novapay_compliance_portal": ["KYC Review", "KYB Review", "AML Alerts", "Case Management"],
    "novapay_finance_portal": ["Settlement Reconciliation", "Ledger Balancing", "Treasury View"],
    "novapay_partner_portal": ["Partner Onboarding", "API Keys", "Webhook Management"],
    "novapay_developer_portal": ["API Documentation", "Sandbox", "OAuth Clients", "Test Transactions"],
    "novapay_support_console": ["Customer Search", "Transaction Lookup", "Dispute Handling", "Account Recovery"],
}

PACKAGES = [
    "novapay-core",
    "novapay-ui",
    "novapay-wallet-sdk",
    "novapay-ledger-sdk",
    "novapay-qr-sdk",
    "novapay-risk-sdk",
    "novapay-receipts-sdk",
    "novapay-auth-sdk",
]


@pytest.mark.parametrize(("directory", "contract"), MOBILE_APPS.items())
def test_mobile_app_package_branding_tabs_and_flows(directory: str, contract: dict[str, object]) -> None:
    app = ROOT / directory
    metadata = json.loads((app / "app.json").read_text())
    gradle = (app / "android/app/build.gradle").read_text()
    strings = (app / "android/app/src/main/res/values/strings.xml").read_text()
    source = "\n".join(path.read_text() for path in (app / "src").glob("*.tsx"))
    source += "\n".join(path.read_text() for path in (app / "src").glob("*.ts"))

    package = str(contract["package"])
    brand = str(contract["brand"])
    assert metadata["expo"]["android"]["package"] == package
    assert f"applicationId '{package}'" in gradle
    assert metadata["expo"]["name"] == brand
    assert brand in strings
    for tab in contract["tabs"]:
        assert tab in source
    for flow in contract["flows"]:
        assert flow in source


def test_consumer_payment_flows_are_wired_and_generate_receipts() -> None:
    source = (ROOT / "novapay_consumer_app/src/roleApp.tsx").read_text()
    assert "onPress={submit}" in source
    assert "setState(\"success\")" in source
    assert "Digital receipt" in source
    assert "Proof-of-payment available" in source
    assert "Transaction timeline" in source
    assert "accessibilityLabel" in source


def test_consumer_australia_to_drc_transfer_scenario_exists() -> None:
    source = (ROOT / "novapay_consumer_app/src/roleApp.tsx").read_text()
    for marker in [
        "Djuma Kikombe",
        "Kaskile Emanuel",
        "Australia",
        "Democratic Republic of Congo",
        "AUD 100.00",
        "AUD 2.99",
        "Mobile Money",
        "NP-2026-00054882",
        "Preparing",
        "Processing",
        "Sent",
        "Delivered",
        "NovaTrust verification",
        "Identity Verified (NovaID)",
        "Ledger Recorded",
        "Replay Evidence Stored",
        "Audit Package Available",
        "Receiver notification",
    ]:
        assert marker in source


def test_agent_cash_in_and_cash_out_are_wired() -> None:
    source = (ROOT / "novapay_agent_app/src/agentApp.tsx").read_text()
    assert '"Cash In"' in source
    assert '"Cash Out"' in source
    assert 'setStage("review")' in source
    assert 'setStage("receipt")' in source
    assert "Receipt" in source


def test_merchant_collection_and_business_approval_are_wired() -> None:
    merchant = (ROOT / "novapay_merchant_app/src/roleApp.tsx").read_text()
    merchant_config = (ROOT / "novapay_merchant_app/src/appConfig.ts").read_text()
    business = (ROOT / "novapay_business_app/src/roleApp.tsx").read_text()
    business_config = (ROOT / "novapay_business_app/src/appConfig.ts").read_text()
    assert "QR Collections" in merchant_config
    assert "onPress={submit}" in merchant
    assert "Approvals" in business_config
    assert "onPress={submit}" in business


@pytest.mark.parametrize(("directory", "features"), PORTALS.items())
def test_portal_surface_exists_and_actions_are_wired(directory: str, features: list[str]) -> None:
    source = (ROOT / directory / "src/app.ts").read_text()
    package = json.loads((ROOT / directory / "package.json").read_text())
    assert package["scripts"]["typecheck"]
    assert "<main aria-label=" in source
    assert "<button aria-label=" in source
    for feature in features:
        assert feature in source


def test_compliance_review_flow_exists() -> None:
    source = (ROOT / "novapay_compliance_portal/src/app.ts").read_text()
    assert "reviewCase" in source
    assert '"approve" | "escalate" | "reject"' in source
    assert "auditEvent" in source


@pytest.mark.parametrize("package", PACKAGES)
def test_shared_package_is_present(package: str) -> None:
    directory = ROOT / "packages" / package
    assert (directory / "package.json").is_file()
    assert (directory / "src/index.ts").is_file()


def test_shared_contracts_cover_required_cross_app_features() -> None:
    combined = "\n".join(
        (ROOT / "packages" / package / "src/index.ts").read_text()
        for package in PACKAGES
    )
    for marker in [
        "NovaIDSession",
        "LedgerEntry",
        "QRPayment",
        "DigitalReceipt",
        "proofOfPayment",
        "AuditEvent",
        "RiskIndicator",
        "offline",
        "ThemeMode",
        "AsyncViewState",
    ]:
        assert marker in combined


def test_no_stale_afriride_branding_in_novapay_sources() -> None:
    roots = [ROOT / directory for directory in [*MOBILE_APPS, *PORTALS]]
    checked_suffixes = {".ts", ".tsx", ".json", ".xml", ".kt", ".gradle"}
    stale: list[str] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in checked_suffixes and "build" not in path.parts:
                if "AfriRide" in path.read_text(errors="ignore"):
                    stale.append(str(path.relative_to(ROOT)))
    assert stale == []
