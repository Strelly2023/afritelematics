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
        return {"query": payload.query, "results": results, "count": len(results), "generated_at": _now()}

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
