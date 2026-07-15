"""Canonical NovaPay ecosystem architecture contract.

This module defines the NovaPay enterprise ecosystem without granting
production readiness or real-money authority. Financial truth remains owned by
NovaPay ledger/runtime services, identity by NovaID, evidence by NovaTrust, and
AI remains advisory-only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class NovaPaySurface:
    name: str
    target_users: tuple[str, ...]
    features: tuple[str, ...]
    channels: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in ("target_users", "features", "channels"):
            payload[key] = list(payload[key])
        return payload


@dataclass(frozen=True, slots=True)
class NovaPayBackendDomain:
    name: str
    owns: tuple[str, ...]
    controls: tuple[str, ...]
    source_of_truth: bool = False

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["owns"] = list(self.owns)
        payload["controls"] = list(self.controls)
        return payload


APPLICATION_SURFACES = (
    NovaPaySurface("Consumer App", ("individuals",), ("registration", "multi-currency wallet", "domestic transfers", "international remittances", "request money", "QR payments", "bill payments", "airtime", "virtual cards", "physical cards", "transaction history", "spending insights", "rewards", "AI assistant", "support"), ("Android", "iOS", "Web", "PWA")),
    NovaPaySurface("Agent App", ("field agents",), ("cash in", "cash out", "customer onboarding", "KYC verification", "wallet funding", "international payouts", "bill payments", "airtime sales", "float management", "commission management", "offline operation", "branch management"), ("Android", "Agent POS", "PWA", "USSD", "SMS")),
    NovaPaySurface("Merchant App", ("shops", "restaurants", "e-commerce"), ("QR payments", "POS payments", "payment links", "online checkout", "refunds", "settlement reports", "sales dashboard", "inventory integration", "loyalty", "invoice generation"), ("Android", "iOS", "Web", "POS")),
    NovaPaySurface("Business App", ("SMEs", "enterprises"), ("business wallet", "multi-user access", "RBAC", "payroll", "supplier payments", "expense management", "bulk payments", "accounting exports", "approval workflows", "treasury management"), ("Web", "PWA", "APIs")),
    NovaPaySurface("Partner Portal", ("banks", "mobile money operators", "fintechs"), ("API onboarding", "API keys", "sandbox", "webhooks", "settlement reports", "reconciliation", "revenue sharing", "analytics", "documentation"), ("Web", "APIs")),
    NovaPaySurface("Operations Portal", ("operations teams",), ("live transaction monitoring", "settlement management", "liquidity management", "reconciliation", "queue monitoring", "incident management", "retry management", "dashboards", "controlled manual intervention"), ("Web",)),
    NovaPaySurface("Compliance Portal", ("compliance officers",), ("KYC review", "KYB review", "AML monitoring", "sanctions screening", "PEP screening", "suspicious activity cases", "regulatory reporting", "case management", "evidence management"), ("Web",)),
    NovaPaySurface("Risk & Fraud Center", ("risk analysts", "fraud analysts"), ("fraud detection", "device fingerprinting", "behavior analytics", "velocity rules", "geolocation analysis", "risk scoring", "transaction blocking", "account monitoring", "AI fraud prediction"), ("Web",)),
    NovaPaySurface("Executive Command Center", ("executives",), ("transaction volume", "revenue", "active customers", "active merchants", "active agents", "FX exposure", "settlement health", "fraud alerts", "availability", "regional performance"), ("Web",)),
    NovaPaySurface("Developer Platform", ("developers", "partners"), ("SDK downloads", "sample apps", "API explorer", "testing tools", "mock servers", "CLI", "Postman collections", "API changelog"), ("Web", "APIs")),
)


BACKEND_DOMAINS = (
    NovaPayBackendDomain("API Gateway", ("TLS termination", "routing", "request validation", "rate limiting", "idempotency enforcement", "correlation IDs"), ("WAF", "API versioning", "partner quotas", "deprecation management")),
    NovaPayBackendDomain("Identity and Access", ("NovaID references", "roles", "sessions", "device trust claims"), ("OAuth 2.1", "OIDC", "RBAC", "ABAC", "session revocation")),
    NovaPayBackendDomain("Customer Profile", ("customer profile", "addresses", "consent", "preferences", "risk profile"), ("lifecycle events", "account status", "verification state")),
    NovaPayBackendDomain("KYC and KYB", ("KYC workflow", "KYB workflow", "verification decisions"), ("sanctions", "PEP", "adverse media", "manual review", "evidence store")),
    NovaPayBackendDomain("Accounts", ("consumer accounts", "business accounts", "merchant accounts", "agent accounts", "settlement accounts", "treasury accounts"), ("restrictions", "limits", "legal holds", "statements")),
    NovaPayBackendDomain("Wallet", ("wallets", "currency pockets", "holds", "reservations", "wallet statements"), ("balance visibility", "wallet limits", "freezing"), source_of_truth=False),
    NovaPayBackendDomain("Double-Entry Ledger", ("ledger accounts", "journals", "journal entries", "postings", "balance snapshots", "reversals"), ("balanced posting", "immutability", "period close", "trial balance", "replay-safe processing"), source_of_truth=True),
    NovaPayBackendDomain("Transfer", ("transfer aggregate", "funding instruction", "payout instruction", "quote snapshot", "status history", "receipt"), ("state machine", "idempotency", "optimistic locking", "risk approval", "compliance approval", "ledger posting")),
    NovaPayBackendDomain("Quote and Pricing", ("quotes", "fees", "tax", "FX margin", "delivery estimate"), ("quote expiration", "price versioning", "calculation audit")),
    NovaPayBackendDomain("Foreign Exchange", ("rates", "rate locks", "exposure", "rate audit"), ("source failover", "manual override approval", "treasury hedge adapters")),
    NovaPayBackendDomain("Funding", ("payment intents", "funding authorization", "card tokenization", "chargeback tracking"), ("3DS", "duplicate prevention", "funding reconciliation")),
    NovaPayBackendDomain("Payout", ("bank payouts", "mobile wallet payouts", "cash pickup", "partner status"), ("retry", "delivery confirmation", "webhook processing", "reconciliation")),
    NovaPayBackendDomain("Risk and Compliance", ("risk decisions", "compliance decisions", "cases", "rules"), ("screening", "transaction monitoring", "step-up", "holds", "blocks")),
    NovaPayBackendDomain("Settlement and Reconciliation", ("settlement instructions", "breaks", "matching", "adjustments"), ("netting", "calendar", "cutoffs", "daily certification")),
    NovaPayBackendDomain("Treasury", ("liquidity", "FX exposure", "forecasting", "prefunding", "position limits"), ("alerts", "hedging recommendations", "approval gates")),
    NovaPayBackendDomain("Cards and QR", ("virtual cards", "physical cards", "QR payloads", "payment requests"), ("tokenization", "card controls", "replay prevention", "receipt generation")),
    NovaPayBackendDomain("Agent and Merchant", ("agents", "branches", "float", "merchants", "stores", "terminals"), ("geofencing", "supervisor approvals", "settlement schedules", "reserve management")),
    NovaPayBackendDomain("Business Payments", ("business users", "approval policies", "payment batches", "payroll", "suppliers", "expenses"), ("maker-checker", "scheduled payments", "accounting export")),
    NovaPayBackendDomain("Support and Disputes", ("support cases", "complaints", "refund requests", "disputes", "chargebacks"), ("SLA", "escalation", "evidence collection", "decision workflows")),
    NovaPayBackendDomain("Partner Integration", ("partner registry", "connectors", "webhooks", "partner reconciliation"), ("credential vault", "circuit breaker", "retry engine", "health monitoring")),
    NovaPayBackendDomain("Event Platform", ("business events", "schema versions", "outbox", "dead letters"), ("idempotent consumers", "replay", "lag monitoring")),
    NovaPayBackendDomain("Workflow Platform", ("long-running transfer workflows", "activities", "compensations"), ("retry", "timeout", "idempotency", "durable orchestration")),
    NovaPayBackendDomain("Document and Evidence", ("documents", "regulatory reports", "signed receipts", "support attachments"), ("encryption", "retention", "legal holds", "malware scanning", "regional storage")),
    NovaPayBackendDomain("Reporting and Analytics", ("operational reports", "executive reports", "warehouse projections"), ("analytical store separation", "BI", "regulatory reports")),
    NovaPayBackendDomain("AI", ("assistants", "forecasting", "anomaly analysis", "document classification"), ("human approval for high-impact decisions", "audit", "model tracking", "drift monitoring")),
    NovaPayBackendDomain("Audit and Observability", ("audit logs", "metrics", "logs", "traces", "security events"), ("immutability", "independent retention", "dashboarding", "alerts")),
)


FRONTEND_APPS = (
    "novapay-consumer-mobile",
    "novapay-agent-mobile",
    "novapay-merchant-mobile",
    "novapay-consumer-web",
    "novapay-business-web",
    "novapay-partner-web",
    "novapay-operations-web",
    "novapay-compliance-web",
    "novapay-risk-web",
    "novapay-support-web",
    "novapay-executive-web",
)


PRODUCTION_GATES = (
    "Double-entry ledger balances",
    "Idempotent transfer execution",
    "Funding and payout reconciliation",
    "KYC/KYB verification",
    "AML and sanctions screening",
    "Risk decision enforcement",
    "Secrets stored outside source code",
    "Partner retries and circuit breakers",
    "Immutable audit evidence",
    "Backup and restore verified",
    "Disaster-recovery test completed",
    "Real settlement reconciliation completed",
    "Role and tenant isolation tested",
    "Penetration testing completed",
    "Regulatory approval confirmed",
    "Operational runbooks tested",
    "Controlled pilot evidence approved",
)


def novapay_authority_boundaries() -> dict[str, Any]:
    return {
        "NovaPay": ("wallets", "ledger", "transfers", "quotes", "FX", "settlements", "financial workflow", "payment references"),
        "NovaID": ("identity", "authentication", "verification", "RBAC/ABAC claims", "device trust", "session intelligence"),
        "NovaTrust": ("replay verification", "digital receipts", "audit evidence", "integrity verification"),
        "NovaLedger": ("double-entry accounting", "journal posting", "authoritative balances"),
        "NovaNotify": ("push", "SMS", "email", "WhatsApp", "voice", "webhooks"),
        "NovaAI": ("advisory assistance", "fraud prediction", "support summaries", "forecasting"),
        "forbidden": (
            "frontend_authoritative_balance",
            "wallet_balance_direct_mutation",
            "ai_ledger_posting",
            "ai_high_risk_approval",
            "admin_bypass_financial_chain",
            "partner_bypass_reconciliation",
            "offline_transaction_marked_completed_without_server_confirmation",
        ),
    }


def novapay_constitutional_flow() -> tuple[str, ...]:
    return (
        "Request",
        "Authenticate",
        "Authorize",
        "Validate jurisdiction and corridor",
        "Generate quote",
        "Evaluate risk and compliance",
        "Reserve funds",
        "Post balanced ledger entries",
        "Execute partner instruction",
        "Reconcile",
        "Generate signed receipt",
        "Record immutable evidence",
    )


def novapay_data_platform() -> dict[str, Any]:
    return {
        "PostgreSQL": "transactional data and ledger",
        "Redis": "cache, locks, rate limits, short-lived sessions",
        "Kafka/Redpanda": "durable business events",
        "Object Storage": "documents, evidence, statements, exports",
        "Search Engine": "operational and audit search",
        "Data Warehouse": "analytics, regulatory reports, executive BI",
        "Secrets Manager": "partner credentials and signing keys",
    }


def novapay_frontend_contract() -> dict[str, Any]:
    return {
        "apps": list(FRONTEND_APPS),
        "shared_packages": ("design-system", "ui-components", "auth-client", "api-client", "analytics", "notifications", "localization", "validation", "security", "feature-flags", "observability", "test-utils"),
        "accessibility": ("WCAG 2.2 AA", "screen readers", "keyboard navigation", "high contrast", "dynamic text sizing", "reduced motion", "focus indicators", "error summaries", "accessible forms"),
        "localization": ("English", "French", "Swahili", "Lingala", "Portuguese", "Arabic", "isiZulu"),
        "offline_rules": (
            "Agent app may cache dashboard and queue drafts using encrypted local storage.",
            "Offline queued financial transactions must not be shown as completed until server confirmation.",
            "Frontend must never invent balances, fees, transfer states, compliance decisions, settlement results, or receipts.",
        ),
        "security": ("secure token storage", "refresh-token rotation", "device binding", "certificate pinning where appropriate", "session timeout", "CSP", "CSRF protection", "XSS protection", "dependency scanning"),
        "production_gates": (
            "Consumer send-money journey passes",
            "Agent cash-in/cash-out journey passes",
            "Merchant payment journey passes",
            "Business approval journey passes",
            "KYC onboarding passes",
            "Accessibility audit passes",
            "Localization verified",
            "Offline behavior verified",
            "Authentication and session security verified",
            "No secrets embedded in bundles",
            "Crash reporting enabled",
            "Performance budgets pass",
            "API contract tests pass",
            "Device certification completed",
            "Browser compatibility completed",
            "Production monitoring enabled",
        ),
    }


def novapay_backend_contract() -> dict[str, Any]:
    return {
        "service_boundaries": (
            "novapay-api",
            "novapay-identity",
            "novapay-customer",
            "novapay-wallet-ledger",
            "novapay-transfer",
            "novapay-risk-compliance",
            "novapay-agent-merchant",
            "novapay-settlement-reconciliation",
            "novapay-notification",
            "novapay-reporting",
            "novapay-integration",
        ),
        "minimum_database_domains": (
            "identity",
            "customers",
            "organizations",
            "accounts",
            "wallets",
            "ledger",
            "transfers",
            "recipients",
            "quotes",
            "fx",
            "funding",
            "payouts",
            "agents",
            "merchants",
            "businesses",
            "cards",
            "compliance",
            "risk",
            "settlements",
            "reconciliation",
            "support",
            "notifications",
            "audit",
            "integrations",
            "reports",
        ),
        "domains": [domain.to_dict() for domain in BACKEND_DOMAINS],
    }


def novapay_production_gate_report() -> dict[str, Any]:
    return {
        "status": "PRODUCTION_NOT_APPROVED",
        "real_payments_enabled": False,
        "gates": [{"gate": gate, "implemented": True, "verified": False, "approved": False} for gate in PRODUCTION_GATES],
    }


def novapay_ecosystem_contract() -> dict[str, Any]:
    return {
        "platform": "NovaPay Enterprise Financial Ecosystem",
        "status": "ARCHITECTURE_CONTRACT_COMPLETE_RUNTIME_AND_APPROVAL_GATES_REQUIRED",
        "surfaces": [surface.to_dict() for surface in APPLICATION_SURFACES],
        "backend": novapay_backend_contract(),
        "frontend": novapay_frontend_contract(),
        "authority_boundaries": novapay_authority_boundaries(),
        "constitutional_flow": list(novapay_constitutional_flow()),
        "data_platform": novapay_data_platform(),
        "production_gates": novapay_production_gate_report(),
    }
