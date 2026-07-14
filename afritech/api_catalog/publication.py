"""Domain OpenAPI publication and signing."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

from afritech.api_catalog.authority import authority_extension, evidence_extension
from afritech.api_catalog.domains import ApiContract, DomainEndpoint
from afritech.api_catalog.provenance import publication_provenance, validate_publication_provenance
from afritech.api_catalog.sdk import sdk_compatibility
from afritech.api_catalog.signing import get_signing_backend


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sha256(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def response_envelope_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["data", "meta", "errors"],
        "properties": {
            "data": {"type": ["object", "null"]},
            "meta": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "trace_id": {"type": "string"},
                    "contract_version": {"type": "string"},
                    "organization_id": {"type": ["string", "null"]},
                },
            },
            "evidence": {"type": ["object", "null"]},
            "errors": {"type": "array", "items": {"$ref": "#/components/schemas/NovaTechError"}},
        },
    }


def error_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["error"],
        "properties": {
            "error": {
                "type": "object",
                "required": ["code", "message", "trace_id", "retryable"],
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {"type": "object"},
                    "trace_id": {"type": "string"},
                    "retryable": {"type": "boolean"},
                },
            }
        },
    }


def _operation(contract: ApiContract, endpoint: DomainEndpoint) -> dict[str, Any]:
    operation = {
        "operationId": endpoint.operation_id,
        "summary": endpoint.summary,
        "description": endpoint.summary,
        "deprecated": endpoint.deprecated,
        "x-novatech-domain": contract.domain,
        "x-novatech-maturity": {
            "status": contract.maturity,
            "introduced": contract.version,
            "supported-until": contract.supported_until,
        },
        "x-novatech-audience": list(endpoint.audience),
        "x-novatech-authority": authority_extension(endpoint),
        "x-novatech-evidence": evidence_extension(endpoint),
        "x-novatech-risk": {
            "level": endpoint.risk_level,
            "idempotency-required": endpoint.idempotency_required,
        },
        "responses": {
            "200": {
                "description": "Standard NovaTech response envelope.",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/NovaTechEnvelope"}}},
            },
            "default": {
                "description": "Standard NovaTech error envelope.",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/NovaTechErrorEnvelope"}}},
            },
        },
    }
    if endpoint.deprecated:
        operation["x-replaced-by"] = endpoint.replaced_by
        operation["x-removal-version"] = endpoint.removal_version
    return operation


def build_domain_openapi(contract: ApiContract) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for endpoint in contract.endpoints:
        path_item = paths.setdefault(endpoint.path, {})
        path_item[endpoint.method.lower()] = _operation(contract, endpoint)
    return {
        "openapi": "3.1.0",
        "info": {
            "title": f"NovaTech {contract.domain} API",
            "version": contract.version,
            "description": contract.description,
            "x-novatech-owner": contract.owner,
            "x-novatech-authority": contract.authority,
            "x-novatech-maturity": contract.maturity,
            "x-novatech-supported-until": contract.supported_until,
        },
        "paths": paths,
        "components": {
            "schemas": {
                "NovaTechEnvelope": response_envelope_schema(),
                "NovaTechErrorEnvelope": error_schema(),
                "NovaTechError": error_schema()["properties"]["error"],
            }
        },
        "x-novatech-domain": contract.domain,
        "x-novatech-audience": list(contract.audience),
        "x-novatech-sdk-targets": list(contract.sdk_targets),
    }


def signed_publication(contract: ApiContract) -> dict[str, Any]:
    openapi = build_domain_openapi(contract)
    provenance = publication_provenance(contract)
    production = os.getenv("NOVATECH_ENVIRONMENT", "development").lower() == "production"
    provenance_issues = validate_publication_provenance(provenance, production=production)
    if provenance_issues:
        raise RuntimeError(f"production_api_contract_provenance_incomplete:{','.join(provenance_issues)}")
    signed_payload = {
        "platform": "NovaTech",
        "domain": contract.domain,
        "version": contract.version,
        "openapi_hash": sha256(openapi),
        "schema_hash": sha256(openapi["components"]["schemas"]),
        "canonicalization": "canonical.v1",
        "sdk_versions": sdk_compatibility(contract),
        "supported_until": contract.supported_until,
        "provenance": provenance,
    }
    signer = get_signing_backend()
    return {**signed_payload, "signature": signer.sign(signed_payload)}
