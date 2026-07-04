"""Role-specific NovaPay surface manifests.

These are declarative app surfaces only. They do not contain money-movement
logic; that remains in NovaPay Core.
"""

from __future__ import annotations

from typing import Any


APP_SURFACES: tuple[dict[str, Any], ...] = (
    {
        "name": "NovaPay Agent App",
        "role": "agent",
        "surface": "mobile",
        "theme": ["glass", "dark-light", "large-cards", "motion-feedback"],
        "capabilities": [
            "cash_in",
            "cash_out",
            "float_management",
            "kyc",
            "qr_payment",
            "nfc_payment",
            "commission_tracking",
            "offline_queue",
            "supervisor_monitoring",
        ],
        "endpoints": ["/v1/novapay/agents", "/v1/novapay/qr", "/v1/novapay/transfers"],
    },
    {
        "name": "NovaPay Wallet",
        "role": "consumer",
        "surface": "mobile",
        "theme": ["glass", "dark-light", "dynamic-gradients", "accessibility-first"],
        "capabilities": [
            "send",
            "receive",
            "qr",
            "bills",
            "cards",
            "savings",
            "receipts",
            "spending_insights",
            "biometrics",
        ],
        "endpoints": ["/v1/novapay/wallets", "/v1/novapay/transfers", "/v1/novapay/receipts"],
    },
    {
        "name": "NovaPay Business Wallet",
        "role": "business",
        "surface": "web-mobile",
        "theme": ["dashboard", "multi-wallet", "approval-first"],
        "capabilities": [
            "multi_wallets",
            "payroll",
            "invoices",
            "collections",
            "approvals",
            "treasury",
            "reconciliation",
        ],
        "endpoints": ["/v1/novapay/business", "/v1/novapay/payroll", "/v1/novapay/invoices"],
    },
    {
        "name": "NovaPay Merchant App",
        "role": "merchant",
        "surface": "mobile-web-pos",
        "theme": ["pos", "inventory", "loyalty", "settlement"],
        "capabilities": [
            "accept_payments",
            "refunds",
            "catalog",
            "inventory",
            "loyalty",
            "settlement",
            "reports",
        ],
        "endpoints": ["/v1/novapay/merchants", "/v1/novapay/refunds", "/v1/novapay/settlements"],
    },
    {
        "name": "NovaPay Corporate Portal",
        "role": "enterprise",
        "surface": "web",
        "theme": ["treasury", "approvals", "compliance", "analytics"],
        "capabilities": [
            "bulk_payments",
            "treasury",
            "payroll",
            "fx",
            "approvals",
            "compliance",
            "reporting",
            "erp_integration",
        ],
        "endpoints": ["/v1/novapay/corporate", "/v1/novapay/payroll", "/v1/novapay/finance"],
    },
    {
        "name": "NovaPay Developer Portal",
        "role": "developer",
        "surface": "web",
        "theme": ["api-console", "sandbox", "contract-verification"],
        "capabilities": [
            "api_keys",
            "oauth_clients",
            "openapi",
            "sdks",
            "sandbox",
            "webhooks",
            "api_analytics",
            "contract_verification",
        ],
        "endpoints": ["/v1/novapay/developer", "/v1/novapay/webhooks", "/v1/novapay/trust"],
    },
)

TRUST_SURFACES: tuple[dict[str, Any], ...] = (
    {
        "name": "Trust Explorer",
        "role": "public",
        "surface": "web",
        "capabilities": ["receipt_verification", "replay_evidence", "proof_hashes", "audit_bundles"],
        "endpoints": ["/v1/novapay/trust", "/v1/novapay/receipts"],
    },
    {
        "name": "Customer Support Console",
        "role": "internal",
        "surface": "web",
        "capabilities": ["incident_review", "customer_lookup", "transaction_review"],
        "endpoints": ["/v1/novapay/operations"],
    },
    {
        "name": "Compliance Portal",
        "role": "internal",
        "surface": "web",
        "capabilities": ["holds", "kyc_review", "audit_exports"],
        "endpoints": ["/v1/novapay/compliance/holds", "/v1/novapay/trust"],
    },
    {
        "name": "Operations Dashboard",
        "role": "internal",
        "surface": "web",
        "capabilities": ["fleet_health", "queue_depth", "delivery_tracking", "incident_monitoring"],
        "endpoints": ["/v1/novapay/operations"],
    },
    {
        "name": "Finance Portal",
        "role": "internal",
        "surface": "web",
        "capabilities": ["reconciliation", "settlement", "reporting"],
        "endpoints": ["/v1/novapay/finance", "/v1/novapay/reconciliation"],
    },
    {
        "name": "Partner Portal",
        "role": "internal",
        "surface": "web",
        "capabilities": ["integration", "certification", "webhooks"],
        "endpoints": ["/v1/novapay/developer", "/v1/novapay/webhooks"],
    },
    {
        "name": "Inspector Portal",
        "role": "public",
        "surface": "web",
        "capabilities": ["evidence_review", "proof_lookup"],
        "endpoints": ["/v1/novapay/trust"],
    },
)


def build_app_surfaces() -> list[dict[str, Any]]:
    return [dict(surface) for surface in APP_SURFACES]


def build_trust_surfaces() -> list[dict[str, Any]]:
    return [dict(surface) for surface in TRUST_SURFACES]
