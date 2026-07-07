from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_dashboard_renders_required_navigation_and_primary_actions() -> None:
    source = read("src/agentApp.tsx")

    for item in (
        "Home",
        "Transfers",
        "Transactions",
        "Float",
        "Profile",
        "Send Money",
        "Receive Money",
        "Cash In",
        "Cash Out",
        "Scan QR",
        "Verify Customer",
        "AgentHomeDashboard",
        "PrimaryActionGrid",
    ):
        assert item in source


def test_agent_app_includes_required_governance_components() -> None:
    source = read("src/agentApp.tsx")

    for item in (
        "CustomerVerificationCard",
        "FloatSummaryCard",
        "TransactionTimeline",
        "OfflineQueuePanel",
        "ReceiptVerificationCard",
        "CommissionSummaryCard",
        "ComplianceAlertPanel",
        "NovaAIInsightCard",
        "AgentProfileScreen",
        "TrustBadge",
        "PilotModeBanner",
        "SyncStatusChip",
        "DeviceTrustChip",
    ):
        assert item in source


def test_agent_app_boundary_language_is_explicit() -> None:
    source = read("src/agentApp.tsx")

    for item in (
        "NovaPay Core processes the transaction after governed approval.",
        "NovaID verification required before submission.",
        "NovaPower authorization required",
        "NovaAI is advisory only and never executes transactions.",
        "UI may not calculate settlement, execute ledger writes, approve transactions, or bypass policy checks.",
        "Alerts originate from NovaPower. UI cannot override holds.",
        "Advisory Only",
    ):
        assert item in source


def test_agent_app_contracts_include_required_endpoints() -> None:
    source = read("src/agentApp.tsx")

    for item in (
        "/v1/novapay/agents/profile",
        "/v1/novapay/agents/float",
        "/v1/novapay/agents/send-money",
        "/v1/novapay/agents/receive-money",
        "/v1/novapay/agents/cash-in",
        "/v1/novapay/agents/cash-out",
        "/v1/novapay/agents/qr",
        "/v1/novapay/agents/kyc",
        "/v1/novapay/agents/commissions",
        "/v1/novapay/agents/settlement",
        "/v1/novapay/agents/history",
        "/v1/novapay/agents/offline-queue",
        "/v1/novapay/agents/sync",
        "/v1/novapay/agents/compliance",
        "/v1/novapay/agents/receipts",
        "/v1/novapay/agents/supervisor-review",
    ):
        assert item in source


def test_agent_app_has_no_execution_client_logic() -> None:
    source = read("src/agentApp.tsx")

    assert "fetch(" not in source
    assert "transfer_money(" not in source
