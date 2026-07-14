"""Federated NovaTech API catalog and contract publication endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from afritech.api_catalog.enforcement import enforce_response_contract
from afritech.api_catalog.metrics import prometheus_metrics
from afritech.api_catalog.publication import response_envelope_schema
from afritech.api_catalog.registry import ApiCatalog, get_api_catalog


def _catalog() -> ApiCatalog:
    return get_api_catalog()


def _domain_response(domain: str, callback) -> dict[str, Any]:
    try:
        return callback(_catalog(), domain)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown_api_domain:{domain}") from exc


def build_api_catalog_router() -> APIRouter:
    router = APIRouter(tags=["api-catalog"])

    @router.get("/v1/platform/api-catalog")
    def list_api_catalog() -> dict[str, Any]:
        return _catalog().list_contracts()

    @router.get("/v1/platform/api-catalog/{domain}")
    def get_api_contract(domain: str) -> dict[str, Any]:
        return _domain_response(domain, lambda catalog, key: catalog.contract_detail(key))

    @router.get("/v1/platform/api-catalog/{domain}/versions")
    def get_api_contract_versions(domain: str) -> dict[str, Any]:
        return _domain_response(domain, lambda catalog, key: catalog.versions(key))

    @router.get("/v1/platform/api-catalog/{domain}/publication")
    @enforce_response_contract(schema=response_envelope_schema(), operation_id="getApiContractPublication", mode="warn")
    def get_api_contract_publication(domain: str) -> dict[str, Any]:
        return _domain_response(domain, lambda catalog, key: catalog.publication(key))

    @router.get("/v1/platform/api-catalog/{domain}/approval")
    def get_api_contract_approval(domain: str) -> dict[str, Any]:
        return _domain_response(domain, lambda catalog, key: catalog.approval(key))

    @router.get("/v1/platform/releases")
    def list_platform_releases() -> dict[str, Any]:
        return _catalog().releases()

    @router.get("/v1/platform/compatibility")
    def get_platform_compatibility() -> dict[str, Any]:
        return _catalog().compatibility()

    @router.get("/v1/platform/deprecations")
    def list_platform_deprecations() -> dict[str, Any]:
        return _catalog().deprecations()

    @router.get("/v1/platform/migrations")
    def list_platform_migrations() -> dict[str, Any]:
        return _catalog().migrations()

    @router.get("/v1/platform/developer-portal")
    def get_developer_portal_navigation() -> dict[str, Any]:
        domains = _catalog().list_contracts()["domains"]
        return {
            "title": "NovaTech Developer Portal",
            "sections": [
                "Choose Product",
                "Quick Start",
                "Authentication",
                "API Reference",
                "SDKs",
                "Webhooks",
                "Sandbox",
                "Errors",
                "Versioning",
                "Migration Guides",
                "Status",
                "Certification",
            ],
            "products": [
                {
                    "domain": domain["domain"],
                    "maturity": domain["maturity"],
                    "audience": domain["audience"],
                    "openapi_url": domain["openapi_url"],
                    "publication_url": domain["signed_publication_url"],
                }
                for domain in domains
            ],
        }

    @router.get("/v1/platform/api-scorecard")
    def get_api_scorecard() -> dict[str, Any]:
        return _catalog().scorecards()

    @router.get("/v1/platform/api-scorecard/{domain}")
    def get_api_domain_scorecard(domain: str) -> dict[str, Any]:
        return _domain_response(domain, lambda catalog, key: catalog.scorecard(key))

    @router.get("/v1/platform/architecture/verify")
    def verify_platform_architecture() -> dict[str, Any]:
        return _catalog().architecture_verification()

    @router.get("/v1/platform/api-metrics", response_class=PlainTextResponse)
    def get_api_metrics() -> str:
        return prometheus_metrics()

    @router.get("/openapi/{domain}.json")
    def get_domain_openapi(domain: str) -> dict[str, Any]:
        return _domain_response(domain, lambda catalog, key: catalog.openapi(key))

    @router.get("/v1/partner/certification/status")
    def get_partner_certification_status() -> dict[str, Any]:
        return {
            "partner_id": "current_partner",
            "lifecycle": [
                "Registered",
                "Sandbox Enabled",
                "Contract Compatible",
                "Security Verified",
                "Webhook Verified",
                "Load Tested",
                "Certified",
                "Production Enabled",
            ],
            "status": "Sandbox Enabled",
            "production_enabled": False,
            "contract_catalog_domain": "partner",
        }

    @router.post("/v1/partner/certification/run")
    def run_partner_certification() -> dict[str, Any]:
        publication = _catalog().publication("partner")
        return {
            "partner_id": "current_partner",
            "status": "Contract Compatible",
            "checks": {
                "catalog_contract_present": True,
                "governance_extensions_present": True,
                "webhook_verification": "PENDING",
                "load_test": "PENDING",
            },
            "evidence": {
                "contract_publication_hash": publication["openapi_hash"],
                "signature_key_id": publication["signature"]["key_id"],
            },
            "production_enabled": False,
        }

    @router.get("/v1/partner/certification/evidence")
    def get_partner_certification_evidence() -> dict[str, Any]:
        return {
            "partner_id": "current_partner",
            "evidence_status": "CATALOG_VERIFIED",
            "publication": _catalog().publication("partner"),
            "production_enabled": False,
        }

    return router
