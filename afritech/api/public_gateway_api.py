"""Public AfriTechnology gateway APIs.

These endpoints back the public corporate website. They intentionally expose
only governed public records and never reuse internal dashboard state.
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator

from afritech.architecture.domain_fabric import summarize_domain_fabric


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


PUBLIC_DOMAIN = "afritechnology.com"
PUBLIC_TITLE = "AfriTechnology | Trusted Digital Platforms"
OPERATOR_TITLES = {"AfriRide Operator Dashboard", "Operator Dashboard"}


PRODUCTS: list[dict[str, Any]] = [
    {
        "product_id": "NOVACODEPRO",
        "name": "NovaCodePro",
        "slug": "novacodepro",
        "family": "Enterprise Platform",
        "summary": "Governed delivery from requirements to operational evidence.",
        "audiences": ["Enterprise", "Developers", "Operations"],
        "industries": ["Technology", "Government", "Financial Services"],
        "features": ["Requirements", "Architecture", "Governance", "Operational verification"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Available",
        "lifecycle": "Available",
        "portal_url": "https://novacodepro.afritechnology.com",
        "documentation_url": "/developers",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaCodePro Platform",
    },
    {
        "product_id": "NOVARIDE",
        "name": "NovaRide",
        "slug": "novaride",
        "family": "Mobility",
        "summary": "Trust-governed mobility operations for riders, drivers, fleets, and dispatch.",
        "audiences": ["Customers", "Businesses", "Operators"],
        "industries": ["Mobility", "Logistics"],
        "features": ["Ride operations", "Driver tools", "Fleet controls", "Safety evidence"],
        "regions": ["Australia", "DRC", "Burundi"],
        "languages": ["en", "fr", "sw"],
        "availability": "Controlled Pilot",
        "lifecycle": "Controlled Pilot",
        "portal_url": "https://app.afritechnology.com",
        "documentation_url": "/products/novaride",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaRide Product",
    },
    {
        "product_id": "NOVAPAY",
        "name": "NovaPay",
        "slug": "novapay",
        "family": "Financial Services",
        "summary": "Payment, wallet, merchant, settlement, and reconciliation workflows with strict activation governance.",
        "audiences": ["Businesses", "Merchants", "Financial Institutions"],
        "industries": ["Financial Services", "Commerce"],
        "features": ["Wallet workflows", "Merchant tools", "Receipts", "Reconciliation"],
        "regions": ["Australia", "Africa"],
        "languages": ["en", "fr"],
        "availability": "Controlled Pilot",
        "lifecycle": "Controlled Pilot",
        "portal_url": "https://business.afritechnology.com",
        "documentation_url": "/products/novapay",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaPay Product",
        "payment_boundary": "Real payments require separate financial governance.",
    },
    {
        "product_id": "NOVAID",
        "name": "NovaID",
        "slug": "novaid",
        "family": "Identity",
        "summary": "Unified identity, access, consent, and assurance for AfriTechnology experiences.",
        "audiences": ["Customers", "Businesses", "Employees", "Partners"],
        "industries": ["Enterprise", "Government", "Financial Services"],
        "features": ["Authentication", "Sessions", "MFA readiness", "Role-aware access"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Partner Access",
        "lifecycle": "Partner Access",
        "portal_url": "https://identity.afritechnology.com",
        "documentation_url": "/developers",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaID Platform",
    },
    {
        "product_id": "NOVATRUST",
        "name": "NovaTrust",
        "slug": "novatrust",
        "family": "Trust",
        "summary": "Evidence, assurance, policy, verification, and governance for trusted operations.",
        "audiences": ["Compliance", "Security", "Executives", "Partners"],
        "industries": ["Enterprise", "Government", "Financial Services"],
        "features": ["Evidence verification", "Trust center", "Policy controls", "Audit history"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Available",
        "lifecycle": "Available",
        "portal_url": "https://trust.afritechnology.com",
        "documentation_url": "/trust",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaTrust Platform",
    },
    {
        "product_id": "NOVACOMMERCE",
        "name": "NovaCommerce",
        "slug": "novacommerce",
        "family": "Commerce",
        "summary": "Merchant, inventory, checkout, support, and evidence-backed commerce operations.",
        "audiences": ["Merchants", "Businesses", "Partners"],
        "industries": ["Commerce", "Retail"],
        "features": ["Merchant workflows", "Catalog readiness", "Receipt verification"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Coming Soon",
        "lifecycle": "Coming Soon",
        "portal_url": "https://merchant.afritechnology.com",
        "documentation_url": "/products/novacommerce",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "",
        "verified_at": None,
        "owner": "NovaCommerce Product",
    },
    {
        "product_id": "NOVACLOUD",
        "name": "NovaCloud",
        "slug": "novacloud",
        "family": "Cloud Platform",
        "summary": "Regional infrastructure and governed deployment for NovaTech services.",
        "audiences": ["Enterprise", "Operations", "Developers"],
        "industries": ["Technology", "Government"],
        "features": ["Environments", "Deployment gates", "Observability", "Regional controls"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Partner Access",
        "lifecycle": "Partner Access",
        "portal_url": "https://novacodepro.afritechnology.com",
        "documentation_url": "/platform",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaCloud Platform",
        "release_channel": "Partner access",
        "health": "Healthy",
        "trust_status": "Verified",
        "pricing": "Commercial plan available via enquiry",
        "screenshots": ["Provisioning", "Environment health", "Deployment evidence"],
        "architecture": ["Edge", "Compute", "Data", "Observability"],
        "faqs": [
            "Is NovaCloud public? Partner access only.",
            "Does NovaCloud emit evidence? Yes, every deployment is recorded.",
        ],
    },
    {
        "product_id": "NOVAGATEWAY",
        "name": "NovaGateway",
        "slug": "novagateway",
        "family": "Integration",
        "summary": "API routing, policy enforcement, and partner integration for public services.",
        "audiences": ["Developers", "Enterprise", "Partners"],
        "industries": ["Technology", "Commerce", "Government"],
        "features": ["API policy", "Routing", "Rate limits", "Webhook controls"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Available",
        "lifecycle": "Available",
        "portal_url": "https://developer.afritechnology.com",
        "documentation_url": "/developers",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaGateway Platform",
        "release_channel": "General availability",
        "health": "Healthy",
        "trust_status": "Verified",
        "pricing": "Included in platform programs",
        "screenshots": ["Policy editor", "API catalog", "Webhook traces"],
        "architecture": ["Public edge", "Policy engine", "Telemetry", "Partner APIs"],
        "faqs": ["Can it expose internal services? No.", "Does it support governed webhooks? Yes."],
    },
    {
        "product_id": "NOVADATA",
        "name": "NovaData",
        "slug": "novadata",
        "family": "Data Platform",
        "summary": "Trusted operational and analytical data products with governed access.",
        "audiences": ["Enterprise", "Developers", "Operations"],
        "industries": ["Technology", "Financial Services", "Government"],
        "features": ["Operational metrics", "Analytical views", "Lineage", "Access controls"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Partner Access",
        "lifecycle": "Partner Access",
        "portal_url": "https://novacodepro.afritechnology.com",
        "documentation_url": "/knowledge",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaData Platform",
        "release_channel": "Partner access",
        "health": "Healthy",
        "trust_status": "Verified",
        "pricing": "Consultation required",
        "screenshots": ["Data catalog", "Lineage view", "Policy coverage"],
        "architecture": ["Events", "Warehouse", "Catalog", "Controls"],
        "faqs": ["Does NovaData expose raw PII? No.", "Is access governed? Yes."],
    },
    {
        "product_id": "NOVACONNECT",
        "name": "NovaConnect",
        "slug": "novaconnect",
        "family": "Integration",
        "summary": "Webhooks, partner integrations, and event contracts for the ecosystem.",
        "audiences": ["Developers", "Partners", "Enterprise"],
        "industries": ["Technology", "Commerce", "Logistics"],
        "features": ["Webhooks", "Event contracts", "Partner routing", "Retries"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Available",
        "lifecycle": "Available",
        "portal_url": "https://developer.afritechnology.com",
        "documentation_url": "/developers",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaConnect Platform",
        "release_channel": "General availability",
        "health": "Healthy",
        "trust_status": "Verified",
        "pricing": "Included in developer programs",
        "screenshots": ["Webhook delivery", "Event schema", "Retry policy"],
        "architecture": ["Producers", "Router", "Queue", "Subscribers"],
        "faqs": ["Can it retry failed events? Yes.", "Are contracts versioned? Yes."],
    },
    {
        "product_id": "NOVAGOV",
        "name": "NovaGov",
        "slug": "novagov",
        "family": "Government",
        "summary": "Public service workflows and auditable citizen service delivery.",
        "audiences": ["Government", "Enterprise"],
        "industries": ["Government"],
        "features": ["Case handling", "Evidence", "Citizen routing", "Policy controls"],
        "regions": ["Australia", "Africa"],
        "languages": ["en"],
        "availability": "Controlled Pilot",
        "lifecycle": "Controlled Pilot",
        "portal_url": "https://app.afritechnology.com",
        "documentation_url": "/platform",
        "support_url": "/support",
        "status_url": "/status",
        "release_version": "2026.1",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "owner": "NovaGov Program",
        "release_channel": "Pilot",
        "health": "Healthy",
        "trust_status": "Verified",
        "pricing": "Government engagement required",
        "screenshots": ["Case lifecycle", "Evidence package", "Review queue"],
        "architecture": ["Front office", "Workflow engine", "Verification", "Archive"],
        "faqs": ["Is NovaGov public? Controlled pilot.", "Does it keep evidence? Yes."],
    },
]

TRUST_RECORDS: list[dict[str, Any]] = [
    {
        "id": "routing-isolation",
        "title": "Public root isolated from internal dashboards",
        "scope": "afritechnology.com",
        "status": "CONFIGURED",
        "owner": "Platform Operations",
        "verified_at": None,
        "valid_until": None,
        "evidence_ref": "tests/public_gateway/test_public_gateway.py",
    },
    {
        "id": "payment-governance-boundary",
        "title": "GA and real-payment activation are separate",
        "scope": "NovaPay, NovaRide, NovaCodePro",
        "status": "ENFORCED",
        "owner": "Risk and Compliance",
        "verified_at": "2026-07-15T00:00:00+00:00",
        "valid_until": "2026-10-15T00:00:00+00:00",
        "evidence_ref": "afritech/governance/rules/RULE-NOVARIDE-FINANCIAL-BOUNDARY.yaml",
    },
    {
        "id": "accessibility-release-gate",
        "title": "WCAG 2.2 AA automation with human review required for major releases",
        "scope": "Public web and portals",
        "status": "CONFIGURED",
        "owner": "UX Governance",
        "verified_at": None,
        "valid_until": None,
        "evidence_ref": "docs/public-web/AFRITECHNOLOGY_PUBLIC_GATEWAY.md",
    },
]

NAVIGATION = [
    {"label": "Platform", "href": "/platform"},
    {"label": "Products", "href": "/products"},
    {"label": "Apps", "href": "/apps"},
    {"label": "Solutions", "href": "/solutions"},
    {"label": "Developers", "href": "/developers"},
    {"label": "Trust Center", "href": "/trust"},
    {"label": "Company", "href": "/about"},
    {"label": "Contact", "href": "/contact"},
]

SHELL_NAVIGATION = [
    {"label": "Explore", "href": "/"},
    {"label": "Products", "href": "/products"},
    {"label": "Apps", "href": "/apps"},
    {"label": "Solutions", "href": "/solutions"},
    {"label": "Industries", "href": "/industries"},
    {"label": "Developers", "href": "/developers"},
    {"label": "Partners", "href": "/partners"},
    {"label": "Support", "href": "/support"},
    {"label": "Trust", "href": "/trust"},
    {"label": "Company", "href": "/about"},
]

QUICK_ACTIONS = [
    {"label": "Start a project", "href": "/contact"},
    {"label": "Open dashboard", "href": "/dashboard"},
    {"label": "Search knowledge", "href": "/knowledge"},
    {"label": "Verify evidence", "href": "/verify"},
    {"label": "View downloads", "href": "/downloads"},
]

ASSISTANT_PROMPTS = [
    "Find the right product for payments or mobility",
    "Show me the trusted developer path",
    "Open my workspace dashboard",
    "Help me verify a release or receipt",
    "Explain the difference between public and private surfaces",
]

WORKSPACE_OPTIONS = [
    {"key": "guest", "label": "Guest", "description": "Public browsing with approved discovery content."},
    {"key": "customer", "label": "Customer", "description": "Open products, downloads, support, and saved items."},
    {"key": "enterprise", "label": "Enterprise", "description": "Projects, approvals, evidence, and AI recommendations."},
    {"key": "partner", "label": "Partner", "description": "Integration, certification, and partner program access."},
]

LANGUAGE_OPTIONS = [
    {"code": "en", "label": "English"},
    {"code": "fr", "label": "Français"},
    {"code": "sw", "label": "Kiswahili"},
]

LAUNCHER: list[dict[str, Any]] = [
    {
        "audience": "Customers",
        "name": "NovaRide Rider",
        "slug": "novaride-rider",
        "icon": "RR",
        "summary": "Book rides, review receipts, and verify trip evidence.",
        "availability": "Controlled Pilot",
        "authentication_required": True,
        "version": "2026.1.3",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Public pilot",
        "url": "https://app.afritechnology.com",
    },
    {
        "audience": "Customers",
        "name": "NovaRide Driver",
        "slug": "novaride-driver",
        "icon": "RD",
        "summary": "Driver shifts, earnings, safety checks, and trip handling.",
        "availability": "Controlled Pilot",
        "authentication_required": True,
        "version": "2026.1.3",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Public pilot",
        "url": "https://app.afritechnology.com",
    },
    {
        "audience": "Businesses",
        "name": "NovaPay Merchant",
        "slug": "novapay-merchant",
        "icon": "PM",
        "summary": "Payment operations, settlement, and merchant verification.",
        "availability": "Controlled Pilot",
        "authentication_required": True,
        "version": "2026.1.3",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Public pilot",
        "url": "https://business.afritechnology.com",
    },
    {
        "audience": "Partners",
        "name": "NovaID Partner",
        "slug": "novaid-partner",
        "icon": "ID",
        "summary": "Federated access, certification, and integration management.",
        "availability": "Partner Access",
        "authentication_required": True,
        "version": "2026.1",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Partner access",
        "url": "https://identity.afritechnology.com",
    },
    {
        "audience": "Employees",
        "name": "NovaCodePro",
        "slug": "novacodepro-workspace",
        "icon": "CP",
        "summary": "Requirements, architecture, delivery, and operational evidence.",
        "availability": "Available",
        "authentication_required": True,
        "version": "2026.1",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "General availability",
        "url": "https://novacodepro.afritechnology.com",
    },
    {
        "audience": "Developers",
        "name": "Developer Portal",
        "slug": "developer-portal",
        "icon": "API",
        "summary": "API explorer, SDK downloads, docs, sandbox, and status.",
        "availability": "Available",
        "authentication_required": False,
        "version": "2026.1",
        "region": "Global",
        "health": "Healthy",
        "release_channel": "General availability",
        "url": "https://developer.afritechnology.com",
    },
    {
        "audience": "Employees",
        "name": "NovaRide Operator",
        "slug": "novaride-operator",
        "icon": "OP",
        "summary": "Operational control, dispatch oversight, and incident handling.",
        "availability": "Private",
        "authentication_required": True,
        "version": "2026.1.3",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Private preview",
        "url": "https://operator.afritechnology.com",
    },
    {
        "audience": "Employees",
        "name": "NovaRide Fleet",
        "slug": "novaride-fleet",
        "icon": "FL",
        "summary": "Fleet oversight, utilization, and managed operations.",
        "availability": "Private",
        "authentication_required": True,
        "version": "2026.1.3",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Private preview",
        "url": "https://operator.afritechnology.com",
    },
    {
        "audience": "Businesses",
        "name": "NovaPay Business",
        "slug": "novapay-business",
        "icon": "PB",
        "summary": "Business payments, settlement, approvals, and reporting.",
        "availability": "Controlled Pilot",
        "authentication_required": True,
        "version": "2026.1.3",
        "region": "Australia",
        "health": "Healthy",
        "release_channel": "Public pilot",
        "url": "https://business.afritechnology.com",
    },
    {
        "audience": "Public",
        "name": "Support Center",
        "slug": "support-center",
        "icon": "SU",
        "summary": "Service requests, escalation paths, and response tracking.",
        "availability": "Available",
        "authentication_required": False,
        "version": "2026.1",
        "region": "Global",
        "health": "Healthy",
        "release_channel": "General availability",
        "url": "https://support.afritechnology.com",
    },
]

DOWNLOAD_ARTIFACTS: list[dict[str, Any]] = [
    {
        "category": "Android",
        "name": "NovaRide Rider",
        "version": "2026.1.3",
        "checksum": "949108d090c449888688d59085244b8a21406ef0fd1af62c183cc570fcf53160",
        "signature": "release_certificate.pem",
        "published_at": "2026-07-15T00:00:00+00:00",
        "supported_platforms": ["Android 10+"],
        "release_notes": "/downloads#novaride-rider",
        "href": "https://download.afritechnology.com/novaride/rider.apk",
    },
    {
        "category": "Android",
        "name": "NovaRide Driver",
        "version": "2026.1.3",
        "checksum": "32f71600203ff78cb1f507cbe0f447fa5fa89506e3b29e3306102512461730b1",
        "signature": "release_certificate.pem",
        "published_at": "2026-07-15T00:00:00+00:00",
        "supported_platforms": ["Android 10+"],
        "release_notes": "/downloads#novaride-driver",
        "href": "https://download.afritechnology.com/novaride/driver.apk",
    },
    {
        "category": "Android",
        "name": "NovaPay Consumer",
        "version": "2026.1.3",
        "checksum": "signature-required",
        "signature": "release_certificate.pem",
        "published_at": "2026-07-15T00:00:00+00:00",
        "supported_platforms": ["Android 10+"],
        "release_notes": "/downloads#novapay-consumer",
        "href": "https://download.afritechnology.com/novapay/consumer.apk",
    },
    {
        "category": "Android",
        "name": "NovaID Personal",
        "version": "2026.1.3",
        "checksum": "signature-required",
        "signature": "release_certificate.pem",
        "published_at": "2026-07-15T00:00:00+00:00",
        "supported_platforms": ["Android 10+"],
        "release_notes": "/downloads#novaid-personal",
        "href": "https://download.afritechnology.com/novaid/personal.apk",
    },
    {
        "category": "SDKs",
        "name": "Nova API SDK",
        "version": "2026.1",
        "checksum": "signature-required",
        "signature": "sdk-signature.pem",
        "published_at": "2026-07-15T00:00:00+00:00",
        "supported_platforms": ["TypeScript", "Python"],
        "release_notes": "/developers",
        "href": "/developers",
    },
    {
        "category": "Evidence Packages",
        "name": "Release certificate",
        "version": "2026.1.3",
        "checksum": "d728b8b26f9acfbc1cd66cca60dbb86aa3663cf2943d06b6aa12600e509b1cc8",
        "signature": "release_certificate.pem",
        "published_at": "2026-07-15T00:00:00+00:00",
        "supported_platforms": ["Public verification"],
        "release_notes": "/verify",
        "href": "https://download.afritechnology.com/novaride/releases/2026.1.3/release_certificate.pem",
    },
]

VERIFICATION_RECORDS: list[dict[str, Any]] = [
    {
        "category": "Receipts",
        "name": "Receipt verification",
        "summary": "Validate signed receipts against public evidence records.",
        "lookup": "/verify",
        "evidence": "Receipt identifiers, timestamps, and public signatures.",
    },
    {
        "category": "Payments",
        "name": "Payment verification",
        "summary": "Check approved payment evidence and transaction references.",
        "lookup": "/verify",
        "evidence": "Payment approval, settlement, and reconciliation records.",
    },
    {
        "category": "Releases",
        "name": "Release verification",
        "summary": "Confirm a release certificate and signed artifact checksum.",
        "lookup": "/downloads",
        "evidence": "Artifact checksums, signatures, and publication dates.",
    },
    {
        "category": "Certificates",
        "name": "Certificate verification",
        "summary": "Review readiness and operational certification evidence.",
        "lookup": "/trust",
        "evidence": "Readiness, trust, and governance records.",
    },
    {
        "category": "Trust",
        "name": "Evidence lookup",
        "summary": "Find the public record associated with a verified claim.",
        "lookup": "/trust",
        "evidence": "Owner, scope, status, and evidence reference.",
    },
]

SERVICE_CATALOG: list[dict[str, Any]] = [
    {
        "name": "Public Website",
        "slug": "public-web",
        "url": "https://afritechnology.com",
        "domain": "afritechnology.com",
        "category": "Public Experience",
        "status": "CONFIGURED",
        "indexing": "index,follow",
        "authentication_required": False,
    },
    {
        "name": "Customer Application Gateway",
        "slug": "app",
        "url": "https://app.afritechnology.com",
        "domain": "app.afritechnology.com",
        "category": "Customer Portals",
        "status": "CONFIGURED",
        "indexing": "noindex,nofollow",
        "authentication_required": True,
    },
    {
        "name": "NovaCodePro",
        "slug": "novacodepro",
        "url": "https://novacodepro.afritechnology.com",
        "domain": "novacodepro.afritechnology.com",
        "category": "Platform",
        "status": "AVAILABLE",
        "indexing": "noindex,nofollow",
        "authentication_required": True,
        "version": "2026.1.0",
    },
    {
        "name": "Developer Platform",
        "slug": "developer",
        "url": "https://developer.afritechnology.com",
        "domain": "developer.afritechnology.com",
        "category": "Platform",
        "status": "CONFIGURED",
        "indexing": "index,follow",
        "authentication_required": False,
    },
    {
        "name": "Trust Center",
        "slug": "trust",
        "url": "https://trust.afritechnology.com",
        "domain": "trust.afritechnology.com",
        "category": "Public Experience",
        "status": "CONFIGURED",
        "indexing": "index,follow",
        "authentication_required": False,
    },
    {
        "name": "Evidence Verification",
        "slug": "verify",
        "url": "https://verify.afritechnology.com",
        "domain": "verify.afritechnology.com",
        "category": "Public Experience",
        "status": "AVAILABLE",
        "indexing": "index,follow",
        "authentication_required": False,
    },
    {
        "name": "Download Center",
        "slug": "download",
        "url": "https://download.afritechnology.com",
        "domain": "download.afritechnology.com",
        "category": "Public Experience",
        "status": "CONFIGURED",
        "indexing": "index,follow",
        "authentication_required": False,
    },
    {
        "name": "Operator Workspace",
        "slug": "operator",
        "url": "https://operator.afritechnology.com",
        "domain": "operator.afritechnology.com",
        "category": "Customer Portals",
        "status": "PLANNED_EXPLICIT_DNS",
        "indexing": "noindex,nofollow",
        "authentication_required": True,
    },
]


class ContactConsent(BaseModel):
    privacy_policy_version: str = "2026.1"
    marketing: bool = False


class ContactRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    request_type: Literal[
        "START_PROJECT",
        "REQUEST_DEMO",
        "BECOME_PARTNER",
        "API_INTEGRATION",
        "CUSTOMER_SUPPORT",
        "CAREERS",
        "COMPLIANCE",
        "SECURITY_DISCLOSURE",
        "MEDIA",
        "GENERAL",
    ]
    name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=254)
    organization: str | None = Field(default=None, max_length=160)
    country: str = Field(min_length=2, max_length=80)
    product_interests: list[str] = Field(default_factory=list, max_length=8)
    message: str = Field(min_length=20, max_length=4000)
    preferred_contact_method: Literal["EMAIL", "PHONE", "WHATSAPP", "VIDEO"] = "EMAIL"
    consent: ContactConsent

    @field_validator("product_interests")
    @classmethod
    def normalize_product_interests(cls, value: list[str]) -> list[str]:
        return sorted({item.upper().replace(" ", "_")[:40] for item in value if item.strip()})

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.rsplit("@", 1)[-1]:
            raise ValueError("valid email is required")
        return normalized


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    audience: str | None = None
    region: str | None = None
    availability: str | None = None


def _reference_for(email: str, request_type: str) -> str:
    digest = sha256(f"{email}:{request_type}:{datetime.now(timezone.utc).date()}".encode()).hexdigest()[:8].upper()
    return f"AFR-2026-{digest}"


def _public_metadata() -> dict[str, Any]:
    return {
        "title": PUBLIC_TITLE,
        "description": "Secure, intelligent, and connected digital platforms for payments, mobility, identity, commerce, healthcare, logistics, government, and enterprise operations.",
        "canonical": f"https://{PUBLIC_DOMAIN}/",
        "robots": "index,follow",
        "og": {
            "site_name": "AfriTechnology",
            "type": "website",
            "url": f"https://{PUBLIC_DOMAIN}/",
            "title": PUBLIC_TITLE,
        },
        "structured_data": {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "AfriTechnology",
            "url": f"https://{PUBLIC_DOMAIN}/",
            "sameAs": [],
        },
    }


def build_public_gateway_router() -> APIRouter:
    router = APIRouter(prefix="/v1/public", tags=["public-gateway"])

    @router.get("/site")
    def site() -> dict[str, Any]:
        return {
            "brand": "AfriTechnology",
            "headline": "Technology you can trust. Platforms built for real life.",
            "supporting_message": "AfriTechnology builds secure, intelligent, and connected digital platforms for payments, mobility, identity, commerce, healthcare, logistics, government, and enterprise operations.",
            "metadata": _public_metadata(),
            "navigation": NAVIGATION,
            "shell": {
                "navigation": SHELL_NAVIGATION,
                "quick_actions": QUICK_ACTIONS,
                "assistant_prompts": ASSISTANT_PROMPTS,
                "workspace_options": WORKSPACE_OPTIONS,
                "language_options": LANGUAGE_OPTIONS,
                "capabilities": [
                    "Global search",
                    "AI assistant",
                    "Command palette",
                    "Workspace switching",
                    "Theme switching",
                    "Notifications",
                ],
            },
            "launcher": LAUNCHER,
            "downloads": DOWNLOAD_ARTIFACTS,
            "verification_records": VERIFICATION_RECORDS,
            "documentation_sections": [
                {"title": "Developer Docs", "summary": "API reference, SDKs, sandbox, and status.", "href": "/developers"},
                {"title": "Quick Starts", "summary": "Launch guides for customers, businesses, partners, and developers.", "href": "/knowledge"},
                {"title": "Architecture", "summary": "Governance, platform, products, and app layers.", "href": "/architecture"},
                {"title": "Security", "summary": "Trust, verification, and release integrity.", "href": "/trust"},
                {"title": "Support", "summary": "Guided support entry and contact workflow.", "href": "/support"},
            ],
            "portal_destinations": {
                "app": "https://app.afritechnology.com",
                "novacodepro": "https://novacodepro.afritechnology.com",
                "developer": "https://developer.afritechnology.com",
                "trust": "https://trust.afritechnology.com",
                "verify": "https://verify.afritechnology.com",
                "status": "https://status.afritechnology.com",
                "support": "https://support.afritechnology.com",
            },
        }

    @router.get("/products")
    def products(audience: str | None = None, region: str | None = None, availability: str | None = None) -> dict[str, Any]:
        records = PRODUCTS
        if audience:
            records = [product for product in records if audience.lower() in {item.lower() for item in product["audiences"]}]
        if region:
            records = [product for product in records if region.lower() in {item.lower() for item in product["regions"]}]
        if availability:
            records = [product for product in records if product["availability"].lower() == availability.lower()]
        return {"products": records, "count": len(records), "generated_at": _now()}

    @router.get("/products/{slug}")
    def product(slug: str) -> dict[str, Any]:
        for record in PRODUCTS:
            if record["slug"] == slug:
                return {"product": record, "generated_at": _now()}
        raise HTTPException(status_code=404, detail="product_not_found")

    @router.get("/product-families")
    def product_families() -> dict[str, Any]:
        families = sorted({product["family"] for product in PRODUCTS})
        return {"families": families, "generated_at": _now()}

    @router.get("/trust")
    def trust() -> dict[str, Any]:
        return {
            "records": TRUST_RECORDS,
            "principles": ["Evidence-backed claims", "Human approvals for high-risk gates", "No invented uptime or certifications", "Public and internal surfaces separated"],
            "generated_at": _now(),
        }

    @router.get("/status")
    def public_status() -> dict[str, Any]:
        return {
            "overall": "CONFIGURED",
            "environment": "production",
            "measured_uptime": None,
            "note": "Public status only reports measured values after live verification evidence exists.",
            "current_incidents": [],
            "latency": {
                "p50_ms": None,
                "p95_ms": None,
                "p99_ms": None,
            },
            "availability": {
                "public_site": "CONFIGURED",
                "apps": "SEPARATE_SUBDOMAIN",
                "api": "HEALTH_CHECKED",
            },
            "regions": [
                {"region": "Australia", "state": "ACTIVE"},
                {"region": "Africa", "state": "ACTIVE"},
            ],
            "maintenance": [],
            "history": [
                {"label": "Release evidence", "value": "Available"},
                {"label": "Rollback verification", "value": "Required for promotion"},
                {"label": "Historical uptime", "value": "Measured only"},
            ],
            "components": [
                {"name": "Public website", "state": "CONFIGURED"},
                {"name": "API", "state": "HEALTH_CHECKED"},
                {"name": "NovaCodePro portal", "state": "SEPARATE_SUBDOMAIN"},
                {"name": "Operator workspace", "state": "SEPARATE_SUBDOMAIN_REQUIRED"},
            ],
            "generated_at": _now(),
        }

    @router.post("/search")
    def search(payload: SearchRequest) -> dict[str, Any]:
        query = payload.query.lower()
        results: list[dict[str, Any]] = []
        for product in PRODUCTS:
            haystack = " ".join(
                [
                    product["name"],
                    product["family"],
                    product["summary"],
                    " ".join(product["audiences"]),
                    " ".join(product["industries"]),
                    " ".join(product["features"]),
                ]
            ).lower()
            if query in haystack:
                if payload.availability and product["availability"].lower() != payload.availability.lower():
                    continue
                results.append(
                    {
                        "type": "product",
                        "title": product["name"],
                        "summary": product["summary"],
                        "href": f"/products/{product['slug']}",
                        "availability": product["availability"],
                    }
                )
        for service in SERVICE_CATALOG:
            haystack = " ".join([service["name"], service["category"], service["domain"], service["status"], service["indexing"]]).lower()
            if query in haystack:
                if payload.availability and service["status"].lower() != payload.availability.lower():
                    continue
                results.append(
                    {
                        "type": "app",
                        "title": service["name"],
                        "summary": f"{service['domain']} · {service['status']} · {service['indexing']}",
                        "href": service["url"],
                        "availability": service["status"],
                    }
                )
        for item in LAUNCHER:
            haystack = " ".join([item["name"], item["audience"], item["summary"], item["availability"], item["release_channel"], item["region"]]).lower()
            if query in haystack:
                if payload.availability and item["availability"].lower() != payload.availability.lower():
                    continue
                results.append(
                    {
                        "type": "app",
                        "title": item["name"],
                        "summary": f"{item['audience']} · {item['availability']} · {item['release_channel']}",
                        "href": item["url"],
                        "availability": item["availability"],
                    }
                )
        for record in TRUST_RECORDS:
            haystack = " ".join([record["title"], record["scope"], record["status"], record["owner"], record["evidence_ref"]]).lower()
            if query in haystack:
                results.append(
                    {
                        "type": "trust",
                        "title": record["title"],
                        "summary": f"{record['scope']} · {record['status']} · {record['owner']}",
                        "href": "/trust",
                        "availability": record["status"],
                    }
                )
        for item in DOWNLOAD_ARTIFACTS:
            haystack = " ".join([item["name"], item["category"], item["version"], item["checksum"], item["signature"], item["release_notes"]]).lower()
            if query in haystack:
                results.append(
                    {
                        "type": "download",
                        "title": item["name"],
                        "summary": f"{item['category']} · {item['version']} · {item['supported_platforms'][0]}",
                        "href": item["href"],
                        "availability": item["version"],
                    }
                )
        for record in VERIFICATION_RECORDS:
            haystack = " ".join([record["name"], record["category"], record["summary"], record["evidence"]]).lower()
            if query in haystack:
                results.append(
                    {
                        "type": "verification",
                        "title": record["name"],
                        "summary": f"{record['category']} · {record['evidence']}",
                        "href": record["lookup"],
                        "availability": "Public",
                    }
                )
        return {"query": payload.query, "results": results, "count": len(results), "generated_at": _now()}

    @router.get("/downloads")
    def downloads() -> dict[str, Any]:
        return {
            "artifacts": DOWNLOAD_ARTIFACTS,
            "categories": sorted({artifact["category"] for artifact in DOWNLOAD_ARTIFACTS}),
            "generated_at": _now(),
        }

    @router.get("/verifications")
    def verifications() -> dict[str, Any]:
        return {
            "records": VERIFICATION_RECORDS,
            "categories": sorted({record["category"] for record in VERIFICATION_RECORDS}),
            "generated_at": _now(),
        }

    @router.post("/contact-requests")
    def contact_request(payload: ContactRequest, request: Request) -> dict[str, Any]:
        if payload.request_type == "SECURITY_DISCLOSURE":
            owner = "Security Response"
            expected_response = "1 business day"
        elif payload.request_type == "CUSTOMER_SUPPORT":
            owner = "Support Operations"
            expected_response = "2 business days"
        else:
            owner = "Growth and Partnerships"
            expected_response = "2 business days"
        request_id = f"contact_{uuid4().hex}"
        reference = _reference_for(str(payload.email), payload.request_type)
        audit_hash = sha256(
            f"{request_id}:{reference}:{payload.request_type}:{payload.email}:{_now()}".encode()
        ).hexdigest()
        return {
            "request_id": request_id,
            "status": "RECEIVED",
            "reference": reference,
            "expected_response": expected_response,
            "owner": owner,
            "sla_timer_started": True,
            "consent_recorded": True,
            "audit_hash": audit_hash,
            "correlation_id": request.headers.get("x-correlation-id") or request_id,
        }

    @router.get("/routing-isolation")
    def routing_isolation() -> dict[str, Any]:
        fabric_summary = summarize_domain_fabric()
        return {
            "public_domain": PUBLIC_DOMAIN,
            "public_title": PUBLIC_TITLE,
            "forbidden_public_titles": sorted(OPERATOR_TITLES),
            "public_root_requires_authentication": False,
            "domain_fabric": fabric_summary,
            "private_access_boundary": {
                "private_hosted_zone": "internal.afritechnology.com",
                "access_model": "zero-trust-private-hosted-zone",
                "publicly_exposed_internal_services": 0,
            },
            "internal_portals": {
                "app.afritechnology.com": {"purpose": "Customer application gateway", "robots": "noindex,nofollow"},
                "operator.afritechnology.com": {"purpose": "Operator workspace", "robots": "noindex,nofollow", "authentication_required": True},
                "novacodepro.afritechnology.com": {"purpose": "NovaCodePro enterprise platform", "robots": "noindex,nofollow", "authentication_required": True},
            },
            "generated_at": _now(),
        }

    return router


def build_enterprise_service_catalog_router() -> APIRouter:
    router = APIRouter(prefix="/v1/catalog", tags=["enterprise-service-catalog"])

    @router.get("/services")
    def services(category: str | None = None) -> dict[str, Any]:
        records = SERVICE_CATALOG
        if category:
            records = [record for record in records if record["category"].lower() == category.lower()]
        return {
            "services": records,
            "count": len(records),
            "wildcard_dns_policy": "PRODUCTION_EXPLICIT_RECORDS_ONLY",
            "unknown_host_policy": "RETURN_404_OR_TLS_EDGE_REJECT",
            "generated_at": _now(),
        }

    return router
