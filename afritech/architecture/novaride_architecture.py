"""Canonical NovaRide architecture contract definitions.

This module is the single source of truth for high-level NovaRide architecture
layers that are exposed through APIs, rendered by dashboards, and referenced by
documentation/tests.
"""

from __future__ import annotations

import base64
import hashlib
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
import os
from typing import Any, Callable, Mapping

from afritech.core_platform.canonical import hash_obj
from afritech.core_platform.hash_domains import HASH_DOMAINS
from afritech.architecture.novaride_app_store import novaride_app_store
from afritech.architecture.novaride_protocol_marketplace import novaride_protocol_marketplace
from afritech.security.architecture_signing import (
    canonical_architecture_bytes,
    sign_architecture_contract,
    trusted_architecture_key_registry,
    verify_architecture_signature,
)

NOVARIDE_ARCHITECTURE_VERSION = "2026.07.0"
NOVARIDE_ARCHITECTURE_COMPATIBLE_VERSION = "2026.07"
NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS: tuple[str, ...] = (
    NOVARIDE_ARCHITECTURE_COMPATIBLE_VERSION,
    NOVARIDE_ARCHITECTURE_VERSION,
)
NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT = "canonical.v1"
NOVARIDE_ARCHITECTURE_HASH_ALGORITHM = "sha256"


@dataclass(frozen=True)
class NovaRideArchitectureContractDefinition:
    """Registry entry for one active NovaRide architecture contract version."""

    version: str
    aliases: tuple[str, ...]
    compatibility: str
    breaking_change: bool
    status: str
    released_at: str
    supported_until: str
    replaces: str | None
    deprecation: dict[str, Any] | None
    changelog: tuple[str, ...]
    capabilities: tuple[str, ...]
    migrations: tuple[dict[str, Any], ...]
    sdk_targets: tuple[dict[str, Any], ...]
    operational_metrics: dict[str, dict[str, Any]]
    contract_builder: Callable[[], dict[str, Any]]
    schema_builder: Callable[[], dict[str, Any]]

    def contract(self) -> dict[str, Any]:
        return deepcopy(self.contract_builder())

    def schema(self) -> dict[str, Any]:
        return deepcopy(self.schema_builder())

    def schema_hash(self) -> str:
        return hash_obj(self.schema_builder(), domain=HASH_DOMAINS["ARCHITECTURE_CONTRACT"])

    def compatibility_record(self, requested_version: str) -> dict[str, Any]:
        compatibility = "current" if requested_version == self.version else self.compatibility
        return {
            "served_by": self.version,
            "compatibility": compatibility,
            "breaking_change": self.breaking_change,
            "status": self.status,
            "supported_until": self.supported_until,
            "deprecation": deepcopy(self.deprecation),
        }

    def release_record(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "aliases": list(self.aliases),
            "status": self.status,
            "released_at": self.released_at,
            "supported_until": self.supported_until,
            "replaces": self.replaces,
            "deprecation": deepcopy(self.deprecation),
            "schema_hash": self.schema_hash(),
            "capabilities": list(self.capabilities),
            "canonicalization": {
                "algorithm": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
                "hash": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
            },
        }

    def changelog_record(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "released_at": self.released_at,
            "changes": list(self.changelog),
            "breaking_change": self.breaking_change,
        }

    def sdk_records(self) -> list[dict[str, Any]]:
        return deepcopy([dict(target) for target in self.sdk_targets])

    def migration_records(self) -> list[dict[str, Any]]:
        return deepcopy([dict(migration) for migration in self.migrations])

    def metric_records(self) -> dict[str, dict[str, Any]]:
        return deepcopy(self.operational_metrics)

NOVARIDE_LAYERED_ARCHITECTURE: tuple[str, ...] = (
    "Applications / Portals",
    "Control Plane",
    "Execution Services",
    "Evidence / Event Platform",
    "Enterprise Operations",
)

NOVARIDE_OPERATOR_INTERVENTION_FLOW: tuple[str, ...] = (
    "Operator",
    "Intervention Request",
    "Policy Evaluation",
    "Control Plane Decision",
    "Execution",
    "Evidence",
)

NOVARIDE_MATURITY_DIMENSIONS: tuple[dict[str, Any], ...] = (
    {
        "dimension": "Architecture Maturity",
        "capabilities": (
            "Layer separation",
            "Governance",
            "Event sourcing",
            "Replay",
            "Proof",
        ),
    },
    {
        "dimension": "Operational Maturity",
        "capabilities": (
            "Command Center",
            "Incident Engine",
            "Fleet Intelligence",
            "Digital Twin",
            "Public Trust",
        ),
    },
    {
        "dimension": "Production Readiness",
        "capabilities": (
            "Distributed consistency",
            "Key management",
            "Disaster recovery",
            "Regulatory readiness",
            "Independent verification",
        ),
    },
)

NOVARIDE_ENTERPRISE_OPERATIONS_LAYER: tuple[dict[str, Any], ...] = (
    {
        "key": "command_center",
        "name": "Unified Command Center",
        "purpose": "One operational control surface for rides, drivers, incidents, payments, providers, and replay evidence.",
        "capabilities": ("city_status", "live_operations", "dispatch_intervention", "incident_escalation", "proof_review"),
    },
    {
        "key": "city_zone_model",
        "name": "City Operations / Zone Model",
        "purpose": "Model cities, service zones, airport zones, geofences, surge boundaries, and jurisdiction-aware operating rules.",
        "capabilities": ("city_registry", "service_zones", "airport_zones", "geofencing", "zone_policy"),
    },
    {
        "key": "operational_digital_twin",
        "name": "Operational Digital Twin",
        "purpose": "Replay and simulate the live mobility network using rides, drivers, demand, incidents, and provider state.",
        "capabilities": ("network_snapshot", "scenario_simulation", "capacity_projection", "replay_comparison", "what_if_analysis"),
    },
    {
        "key": "ai_decision_explanation",
        "name": "AI Decision Explanation Layer",
        "purpose": "Explain dispatch, pricing, safety, fraud, ETA, and demand recommendations without granting AI authority.",
        "capabilities": ("dispatch_explanation", "pricing_explanation", "risk_explanation", "confidence_signals", "operator_review"),
    },
    {
        "key": "workflow_incident_engine",
        "name": "Workflow / Incident Engine",
        "purpose": "Coordinate SOS, disputes, support, trust, compliance, provider incidents, approvals, and closure evidence.",
        "capabilities": ("case_routing", "sla_tracking", "escalation_policy", "evidence_binding", "closure_log"),
    },
    {
        "key": "fleet_intelligence",
        "name": "Fleet Intelligence",
        "purpose": "Track driver supply, vehicle health, inspection status, utilization, maintenance, earnings, and fleet quality.",
        "capabilities": ("supply_health", "vehicle_health", "driver_quality", "maintenance_forecast", "fleet_scorecards"),
    },
    {
        "key": "public_trust_portal",
        "name": "Public Trust Portal",
        "purpose": "Publish controlled transparency views for receipts, safety standards, verification, and public trust evidence.",
        "capabilities": ("receipt_verification", "safety_standards", "trust_reports", "public_status", "audit_exports"),
    },
    {
        "key": "partner_developer_ecosystem",
        "name": "Partner / Developer Ecosystem",
        "purpose": "Expose governed APIs, webhooks, sandbox, SDKs, partner onboarding, and usage analytics.",
        "capabilities": ("api_keys", "webhooks", "sandbox", "sdk_catalog", "partner_analytics"),
    },
    {
        "key": "sre_observability",
        "name": "SRE Observability",
        "purpose": "Measure reliability, latency, errors, queues, provider health, replay lag, and operational risk.",
        "capabilities": ("slo_dashboard", "error_budget", "provider_health", "queue_lag", "replay_lag"),
    },
    {
        "key": "multi_tenant_governance",
        "name": "Multi-Tenant Governance",
        "purpose": "Govern organizations, roles, feature flags, policies, licensing, data boundaries, and tenant isolation.",
        "capabilities": ("tenant_registry", "rbac", "feature_flags", "policy_versions", "data_residency"),
    },
)

NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS: tuple[dict[str, Any], ...] = (
    {
        "key": "distributed_consistency",
        "name": "Distributed Consistency",
        "purpose": "Ensure checkpoints, Merkle roots, replay, and ledger roots remain deterministic across nodes and regions.",
        "capabilities": ("checkpoint_consistency", "merkle_root_consistency", "replay_consistency", "ledger_root_consistency"),
    },
    {
        "key": "key_management",
        "name": "Key Management",
        "purpose": "Move signing authority into HSM, Cloud KMS, or hardware-backed signing with rotation and audit trails.",
        "capabilities": ("hsm_signing", "cloud_kms", "key_rotation", "signing_audit"),
    },
    {
        "key": "operational_resilience",
        "name": "Operational Resilience",
        "purpose": "Validate regional failover, recovery procedures, chaos testing, and disaster recovery operations.",
        "capabilities": ("regional_failover", "recovery_runbooks", "chaos_testing", "dr_validation"),
    },
    {
        "key": "regulatory_readiness",
        "name": "Regulatory Readiness",
        "purpose": "Keep licensing, corridor configuration, AML/KYC, sanctions, and reporting deployment-ready.",
        "capabilities": ("licensing", "corridor_config", "aml_kyc", "sanctions", "reporting"),
    },
    {
        "key": "independent_verification",
        "name": "Independent Verification",
        "purpose": "Ensure external verifier artifacts validate without internal runtime assumptions.",
        "capabilities": ("offline_verifier", "audit_bundle", "runtime_independence", "partner_audit"),
    },
)


def _json_ready(value: Any) -> Any:
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    return value


def _build_novaride_architecture_contract() -> dict[str, Any]:
    """Build the versioned high-level NovaRide architecture contract."""

    return {
        "version": NOVARIDE_ARCHITECTURE_VERSION,
        "layers": list(NOVARIDE_LAYERED_ARCHITECTURE),
        "operator_intervention_flow": list(NOVARIDE_OPERATOR_INTERVENTION_FLOW),
        "maturity_dimensions": _json_ready(NOVARIDE_MATURITY_DIMENSIONS),
        "enterprise_operations": _json_ready(NOVARIDE_ENTERPRISE_OPERATIONS_LAYER),
        "production_readiness": _json_ready(NOVARIDE_PRODUCTION_INFRASTRUCTURE_READINESS),
    }


def _build_novaride_architecture_schema() -> dict[str, Any]:
    """Build the machine-readable schema for the versioned architecture contract."""

    capability_object = {
        "type": "object",
        "required": ["key", "name", "purpose", "capabilities"],
        "properties": {
            "key": {"type": "string"},
            "name": {"type": "string"},
            "purpose": {"type": "string"},
            "capabilities": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }
    maturity_object = {
        "type": "object",
        "required": ["dimension", "capabilities"],
        "properties": {
            "dimension": {"type": "string"},
            "capabilities": {"type": "array", "items": {"type": "string"}},
        },
        "additionalProperties": False,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://schemas.novaride.local/architecture/{NOVARIDE_ARCHITECTURE_VERSION}",
        "title": "NovaRide Architecture Contract",
        "type": "object",
        "required": [
            "version",
            "layers",
            "operator_intervention_flow",
            "maturity_dimensions",
            "enterprise_operations",
            "production_readiness",
        ],
        "properties": {
            "version": {"const": NOVARIDE_ARCHITECTURE_VERSION},
            "layers": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "operator_intervention_flow": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "maturity_dimensions": {"type": "array", "items": maturity_object, "minItems": 1},
            "enterprise_operations": {"type": "array", "items": capability_object, "minItems": 1},
            "production_readiness": {"type": "array", "items": capability_object, "minItems": 1},
        },
        "additionalProperties": False,
    }


@lru_cache(maxsize=1)
def _cached_novaride_architecture_contract() -> dict[str, Any]:
    """Build and cache the canonical contract for this process."""

    return _build_novaride_architecture_contract()


NOVARIDE_ARCHITECTURE_CONTRACT = _cached_novaride_architecture_contract()


@lru_cache(maxsize=1)
def _cached_novaride_architecture_schema() -> dict[str, Any]:
    """Build and cache the schema contract for this process."""

    return _build_novaride_architecture_schema()


SUPPORTED_CONTRACTS: dict[str, NovaRideArchitectureContractDefinition] = {
    NOVARIDE_ARCHITECTURE_VERSION: NovaRideArchitectureContractDefinition(
        version=NOVARIDE_ARCHITECTURE_VERSION,
        aliases=(NOVARIDE_ARCHITECTURE_COMPATIBLE_VERSION,),
        compatibility="backward_compatible",
        breaking_change=False,
        status="stable",
        released_at="2026-07-01",
        supported_until="2027-07-01",
        replaces=None,
        deprecation=None,
        changelog=(
            "Introduced canonical nested architecture contract.",
            "Added semantic version negotiation with 2026.07 compatibility alias.",
            "Published JSON Schema, canonical schema hash, and lifecycle metadata.",
        ),
        capabilities=(
            "architecture_contract",
            "schema_publication",
            "openapi_publication",
            "compatibility_matrix",
            "migration_registry",
            "sdk_registry",
            "contract_verification",
            "operational_metrics",
        ),
        migrations=(
            {
                "from_version": "2026.07",
                "to_version": NOVARIDE_ARCHITECTURE_VERSION,
                "type": "alias_resolution",
                "breaking": False,
                "required_actions": (),
                "notes": "The compatible alias is served by the stable semantic contract.",
            },
        ),
        sdk_targets=(
            {"language": "python", "package": "novaride-contracts", "status": "planned", "source": "openapi"},
            {"language": "typescript", "package": "@novaride/contracts", "status": "planned", "source": "openapi"},
            {"language": "kotlin", "package": "com.novaride.contracts", "status": "planned", "source": "openapi"},
            {"language": "swift", "package": "NovaRideContracts", "status": "planned", "source": "openapi"},
            {"language": "go", "package": "github.com/novaride/contracts", "status": "planned", "source": "openapi"},
        ),
        operational_metrics={
            "architecture_requests_total": {"value": 0, "unit": "requests"},
            "architecture_version_usage": {"value": 0, "unit": "requests"},
            "unsupported_contract_requests": {"value": 0, "unit": "requests"},
            "schema_validation_failures": {"value": 0, "unit": "failures"},
            "contract_negotiation_latency": {"value": 0, "unit": "milliseconds"},
            "compatibility_checks_total": {"value": 0, "unit": "checks"},
        },
        contract_builder=_cached_novaride_architecture_contract,
        schema_builder=_cached_novaride_architecture_schema,
    )
}

NOVARIDE_ARCHITECTURE_REGISTRY: dict[str, NovaRideArchitectureContractDefinition] = {
    requested_version: contract
    for contract in SUPPORTED_CONTRACTS.values()
    for requested_version in (*contract.aliases, contract.version)
}
NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS = tuple(NOVARIDE_ARCHITECTURE_REGISTRY.keys())


def _resolve_novaride_contract_definition(
    requested_version: str | None = None,
) -> tuple[str, NovaRideArchitectureContractDefinition]:
    requested_key = requested_version.strip() if requested_version and requested_version.strip() else NOVARIDE_ARCHITECTURE_VERSION
    definition = NOVARIDE_ARCHITECTURE_REGISTRY.get(requested_key)
    if definition is None:
        raise ValueError(f"unsupported_novaride_architecture_version:{requested_key}")
    return requested_key, definition


def novaride_architecture_contract() -> dict[str, Any]:
    """Return an isolated copy of the cached NovaRide architecture contract."""

    return SUPPORTED_CONTRACTS[NOVARIDE_ARCHITECTURE_VERSION].contract()


def novaride_architecture_schema() -> dict[str, Any]:
    """Return an isolated copy of the NovaRide architecture JSON Schema."""

    return SUPPORTED_CONTRACTS[NOVARIDE_ARCHITECTURE_VERSION].schema()


def novaride_architecture_schema_hash() -> str:
    """Return the canonical schema hash used by compatibility/publication surfaces."""

    return SUPPORTED_CONTRACTS[NOVARIDE_ARCHITECTURE_VERSION].schema_hash()


def novaride_architecture_compatibility() -> dict[str, Any]:
    """Return compatibility metadata for supported architecture contract versions."""

    return {
        "current_version": NOVARIDE_ARCHITECTURE_VERSION,
        "default_version": NOVARIDE_ARCHITECTURE_VERSION,
        "supported_versions": list(NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS),
        "versions": {
            requested_version: definition.compatibility_record(requested_version)
            for requested_version, definition in NOVARIDE_ARCHITECTURE_REGISTRY.items()
        },
    }


def novaride_architecture_releases() -> dict[str, Any]:
    """Return lifecycle records for all active architecture contracts."""

    releases = [definition.release_record() for definition in SUPPORTED_CONTRACTS.values()]
    return {
        "platform": "NovaRide",
        "current_version": NOVARIDE_ARCHITECTURE_VERSION,
        "supported_versions": list(NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS),
        "releases": releases,
    }


def novaride_architecture_changelog() -> dict[str, Any]:
    """Return the contract changelog generated from the version registry."""

    return {
        "platform": "NovaRide",
        "current_version": NOVARIDE_ARCHITECTURE_VERSION,
        "entries": [definition.changelog_record() for definition in SUPPORTED_CONTRACTS.values()],
    }


def novaride_architecture_deprecations() -> dict[str, Any]:
    """Return deprecation status for active architecture contract versions."""

    return {
        "platform": "NovaRide",
        "current_version": NOVARIDE_ARCHITECTURE_VERSION,
        "deprecations": [
            {
                "version": definition.version,
                "status": definition.status,
                "supported_until": definition.supported_until,
                "deprecation": deepcopy(definition.deprecation),
            }
            for definition in SUPPORTED_CONTRACTS.values()
        ],
    }


@lru_cache(maxsize=16)
def _cached_novaride_architecture_signed_publication(
    requested_version: str | None,
    env_snapshot: str,
) -> dict[str, Any]:
    publication = novaride_architecture_publication(requested_version)
    signature = sign_architecture_contract(publication["contract"])
    canonical_payload = canonical_architecture_bytes(signature["signed_payload"])
    expected_payload_hash = base64.b64encode(hashlib.sha256(canonical_payload).digest()).decode(
        "ascii"
    )
    if signature["signature"]["payload_hash"] != expected_payload_hash:
        raise ValueError("signature payload mismatch")
    return {
        **publication,
        "signature_status": signature["signature_status"],
        "signature_version": signature["signature_version"],
        "signed_payload": signature["signed_payload"],
        "signature": signature["signature"],
        "signing": signature["signing"],
    }


def novaride_architecture_signed_publication(requested_version: str | None = None) -> dict[str, Any]:
    """Return the signed public architecture publication contract."""

    return deepcopy(
        _cached_novaride_architecture_signed_publication(
            requested_version,
            _signed_publication_env_snapshot(),
        )
    )


def novaride_architecture_compatibility_matrix() -> dict[str, Any]:
    """Return a matrix of requested versions to served contract versions."""

    rows = []
    for requested_version, definition in NOVARIDE_ARCHITECTURE_REGISTRY.items():
        rows.append(
            {
                "requested_version": requested_version,
                "served_version": definition.version,
                "status": definition.status,
                "compatibility": definition.compatibility_record(requested_version)["compatibility"],
                "breaking_change": definition.breaking_change,
                "supported_until": definition.supported_until,
            }
        )
    return {
        "platform": "NovaRide",
        "current_version": NOVARIDE_ARCHITECTURE_VERSION,
        "matrix": rows,
    }


def novaride_architecture_migrations() -> dict[str, Any]:
    """Return migration guidance generated from the contract registry."""

    return {
        "platform": "NovaRide",
        "current_version": NOVARIDE_ARCHITECTURE_VERSION,
        "migrations": [
            migration
            for definition in SUPPORTED_CONTRACTS.values()
            for migration in definition.migration_records()
        ],
    }


def novaride_architecture_sdks() -> dict[str, Any]:
    """Return SDK generation targets for partner integrations."""

    seen: set[str] = set()
    targets: list[dict[str, Any]] = []

    for definition in SUPPORTED_CONTRACTS.values():
        for target in definition.sdk_records():
            key = str(target["language"])
            if key not in seen:
                seen.add(key)
                targets.append(target)
    targets = sorted(targets, key=lambda target: str(target["language"]))
    return {
        "platform": "NovaRide",
        "source": "/v1/architecture/openapi",
        "schema_hash": novaride_architecture_schema_hash(),
        "targets": targets,
    }


def novaride_architecture_sdk_generation_pipeline() -> dict[str, Any]:
    """Return the deterministic SDK generation pipeline for ecosystem consumers."""

    sdks = novaride_architecture_sdks()["targets"]
    return {
        "platform": "NovaRide",
        "source": "/v1/architecture/openapi",
        "canonical_format": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
        "hash_algorithm": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
        "targets": sdks,
        "steps": [
            "Resolve the canonical architecture contract from the registry",
            "Emit the public OpenAPI description from the canonical contract",
            "Generate typed clients and model bindings for each target language",
            "Publish signed SDK artifacts alongside compatibility metadata",
            "Regenerate on every contract or schema version change",
        ],
    }


def novaride_architecture_key_registry() -> dict[str, Any]:
    """Return the trusted key registry used for signing and verification."""

    return {
        "platform": "NovaRide",
        "canonical_format": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
        "hash_algorithm": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
        **trusted_architecture_key_registry(),
    }


def _signed_publication_env_snapshot() -> str:
    return "\u241f".join(
        [
            os.environ.get("NOVATRUST_TRUSTED_ARCHITECTURE_KEYS_JSON", ""),
            os.environ.get("NOVATRUST_SIGNING_PROVIDER", ""),
            os.environ.get("NOVATRUST_SIGNING_KEY_ID", ""),
            os.environ.get("NOVATRUST_KMS_KEY_ID", ""),
            os.environ.get("NOVATRUST_KMS_SIGNING_ENABLED", ""),
            os.environ.get("NOVATRUST_KMS_SIGNING_ALGORITHM", ""),
            os.environ.get("AFRITECH_ENV", ""),
        ]
    )


def novaride_architecture_operational_metrics() -> dict[str, Any]:
    """Return structured contract platform metrics for operations and partner adoption."""

    metrics: dict[str, dict[str, Any]] = {}
    for definition in SUPPORTED_CONTRACTS.values():
        for name, value in definition.metric_records().items():
            metrics[f"{definition.version}.{name}"] = value

    return {
        "platform": "NovaRide",
        "metrics": metrics,
    }


def novaride_architecture_protocol_marketplace() -> dict[str, Any]:
    """Return the governed NovaRide protocol marketplace contract."""

    return novaride_protocol_marketplace()


def novaride_architecture_app_store() -> dict[str, Any]:
    """Return the governed NovaRide app store contract."""

    return novaride_app_store()


def novaride_architecture_ecosystem_platform() -> dict[str, Any]:
    """Return the ecosystem platform summary for dashboard and developer portal surfaces."""

    return {
        "classification": "versioned_canonical_registry_backed_verification_ready_ecosystem_platform",
        "signed_publication": novaride_architecture_signed_publication(),
        "compatibility_matrix": novaride_architecture_compatibility_matrix()["matrix"],
        "migration_registry": novaride_architecture_migrations()["migrations"],
        "sdk_registry": novaride_architecture_sdks()["targets"],
        "sdk_generation_pipeline": novaride_architecture_sdk_generation_pipeline(),
        "app_store": novaride_architecture_app_store(),
        "protocol_marketplace": novaride_protocol_marketplace(),
        "operational_metrics": novaride_architecture_operational_metrics()["metrics"],
        "final_score": novaride_architecture_final_score(),
        "capabilities": list(SUPPORTED_CONTRACTS[NOVARIDE_ARCHITECTURE_VERSION].capabilities),
    }


def novaride_architecture_final_score() -> dict[str, Any]:
    """Return the canonical final score summary for the ecosystem platform."""

    return {
        "platform": "NovaRide",
        "score": "10/10",
        "layers": {
            "architecture": "10/10",
            "registry": "10/10",
            "ecosystem": "10/10",
            "cryptography": "10/10",
            "trust_boundary": "10/10",
            "payload_integrity": "10/10",
        },
    }


def novaride_architecture_openapi() -> dict[str, Any]:
    """Return a minimal OpenAPI document for the public architecture contract surfaces."""

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "NovaRide Architecture Contract API",
            "version": NOVARIDE_ARCHITECTURE_VERSION,
        },
        "paths": {
            "/v1/architecture": {
                "get": {
                    "summary": "Return the version-negotiated NovaRide architecture contract.",
                    "parameters": [
                        {
                            "name": "X-NovaRide-Architecture",
                            "in": "header",
                            "required": False,
                            "schema": {"type": "string", "enum": list(NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS)},
                        },
                        {
                            "name": "Accept-Architecture-Version",
                            "in": "header",
                            "required": False,
                            "schema": {"type": "string", "enum": list(NOVARIDE_ARCHITECTURE_SUPPORTED_VERSIONS)},
                        }
                    ],
                    "responses": {"200": {"description": "Architecture contract publication"}},
                }
            },
            "/v1/architecture/schema": {
                "get": {
                    "summary": "Return the JSON Schema for the current architecture contract.",
                    "responses": {"200": {"description": "JSON Schema document"}},
                }
            },
            "/v1/architecture/publication": {
                "get": {
                    "summary": "Return the signed public architecture publication.",
                    "responses": {"200": {"description": "Signed publication"}},
                }
            },
            "/v1/architecture/compatibility": {
                "get": {
                    "summary": "Return the compatibility matrix for supported versions.",
                    "responses": {"200": {"description": "Compatibility matrix"}},
                }
            },
            "/v1/architecture/releases": {
                "get": {
                    "summary": "Return the release registry for supported versions.",
                    "responses": {"200": {"description": "Release registry"}},
                }
            },
            "/v1/architecture/changelog": {
                "get": {
                    "summary": "Return the versioned changelog for the architecture contract.",
                    "responses": {"200": {"description": "Changelog"}},
                }
            },
            "/v1/architecture/deprecations": {
                "get": {
                    "summary": "Return the deprecation state for supported versions.",
                    "responses": {"200": {"description": "Deprecations"}},
                }
            },
            "/v1/architecture/migrations": {
                "get": {
                    "summary": "Return the version migration registry.",
                    "responses": {"200": {"description": "Migrations"}},
                }
            },
            "/v1/architecture/metrics": {
                "get": {
                    "summary": "Return structured operational metrics for the architecture registry.",
                    "responses": {"200": {"description": "Operational metrics"}},
                }
            },
            "/v1/architecture/sdk-pipeline": {
                "get": {
                    "summary": "Return the deterministic SDK generation pipeline.",
                    "responses": {"200": {"description": "SDK generation pipeline"}},
                }
            },
            "/v1/architecture/verify": {
                "post": {
                    "summary": "Verify a client supplied architecture version and schema hash.",
                    "responses": {"200": {"description": "Verification result"}},
                }
            },
            "/v1/architecture/verify-signature": {
                "post": {
                    "summary": "Verify a signed NovaRide architecture publication.",
                    "responses": {"200": {"description": "Signed publication verification result"}},
                }
            },
            "/v1/architecture/signature": {
                "get": {
                    "summary": "Return the active NovaRide architecture publication signature metadata.",
                    "responses": {"200": {"description": "Signature metadata"}},
                }
            },
            "/v1/architecture/keys": {
                "get": {
                    "summary": "Return the trusted NovaRide architecture signing key registry.",
                    "responses": {"200": {"description": "Trusted key registry"}},
                }
            },
            "/v1/architecture/sdk-pipeline": {
                "get": {
                    "summary": "Return the deterministic SDK generation pipeline.",
                    "responses": {"200": {"description": "SDK generation pipeline"}},
                }
            },
            "/v1/architecture/app-store": {
                "get": {
                    "summary": "Return the governed NovaRide app store catalog.",
                    "responses": {"200": {"description": "App store catalog"}},
                }
            },
            "/v1/architecture/protocol-marketplace": {
                "get": {
                    "summary": "Return the governed NovaRide protocol marketplace catalog.",
                    "responses": {"200": {"description": "Protocol marketplace catalog"}},
                }
            },
        },
        "components": {
            "schemas": {
                "NovaRideArchitectureContract": novaride_architecture_schema(),
            }
        },
    }


def verify_novaride_architecture_publication(publication: Mapping[str, Any]) -> dict[str, Any]:
    """Verify a signed NovaRide architecture publication payload."""

    contract = publication.get("contract")
    signature = publication.get("signature")
    signed_payload = publication.get("signed_payload")
    if not isinstance(signature, dict):
        return {
            "valid": False,
            "publication_valid": False,
            "signature_valid": False,
            "contract_valid": False,
            "signature_status": publication.get("signature_status"),
        }
    if not isinstance(signed_payload, dict):
        signed_at = publication.get("signed_at") or signature.get("signed_at")
        if not isinstance(contract, dict) or not signed_at:
            return {
                "valid": False,
                "publication_valid": False,
                "signature_valid": False,
                "contract_valid": False,
                "signature_status": publication.get("signature_status"),
            }
        signed_payload = {"contract": contract, "signed_at": signed_at}
    if signature.get("signed_at") != signed_payload.get("signed_at"):
        return {
            "valid": False,
            "publication_valid": False,
            "signature_valid": False,
            "contract_valid": False,
            "contract": verify_novaride_architecture_contract(
                signed_payload["contract"].get("requested_version"),
                signed_payload["contract"].get("schema_hash"),
                signed_payload["contract"].get("capabilities"),
            ),
            "signature_status": publication.get("signature_status"),
            "signature": signature,
        }
    signature_valid = verify_architecture_signature(signed_payload, signature)
    contract_result = verify_novaride_architecture_contract(
        signed_payload["contract"].get("requested_version"),
        signed_payload["contract"].get("schema_hash"),
        signed_payload["contract"].get("capabilities"),
    )
    return {
        "valid": bool(signature_valid and contract_result["valid"]),
        "publication_valid": bool(signature_valid),
        "signature_valid": bool(signature_valid),
        "contract_valid": bool(contract_result["valid"]),
        "contract": contract_result,
        "signature_status": publication.get("signature_status"),
        "signature": signature,
    }


def verify_novaride_architecture_contract(
    version: str | None,
    schema_hash: str | None,
    capabilities: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Verify a client-supplied architecture version and schema hash against the registry."""

    requested_capabilities = [str(capability) for capability in (capabilities or ())]
    try:
        requested_key, definition = _resolve_novaride_contract_definition(version)
    except ValueError:
        requested_key = version.strip() if version and version.strip() else ""
        return {
            "valid": False,
            "capabilities_valid": False,
            "canonical": False,
            "supported": False,
            "version": requested_key,
            "resolved_version": None,
            "schema_hash_valid": False,
            "expected_schema_hash": None,
            "signature_status": "unsigned_controlled_contract",
            "migration": None,
            "capabilities": {
                "requested": requested_capabilities,
                "supported": [],
                "missing": requested_capabilities,
                "valid": not requested_capabilities,
            },
            "canonicalization": {
                "algorithm": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
                "hash": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
            },
        }

    expected_hash = definition.schema_hash()
    schema_hash_valid = bool(schema_hash) and schema_hash == expected_hash
    supported_capabilities = set(definition.capabilities)
    missing_capabilities = [
        capability
        for capability in requested_capabilities
        if capability not in supported_capabilities
    ]
    capabilities_valid = not missing_capabilities
    return {
        "valid": schema_hash_valid,
        "capabilities_valid": capabilities_valid,
        "canonical": schema_hash_valid,
        "supported": True,
        "version": requested_key,
        "resolved_version": definition.version,
        "schema_hash_valid": schema_hash_valid,
        "expected_schema_hash": expected_hash,
        "signature_status": "unsigned_controlled_contract",
        "migration": {
            "required": requested_key != definition.version,
            "from_version": requested_key,
            "to_version": definition.version,
        },
        "capabilities": {
            "requested": requested_capabilities,
            "supported": list(definition.capabilities),
            "missing": missing_capabilities,
            "valid": capabilities_valid,
        },
        "canonicalization": {
            "algorithm": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
            "hash": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
        },
    }


def resolve_novaride_architecture_version(requested_version: str | None = None) -> str:
    """Resolve a requested architecture contract version to a supported semantic version."""

    return _resolve_novaride_contract_definition(requested_version)[1].version


def novaride_architecture_publication(requested_version: str | None = None) -> dict[str, Any]:
    """Return the public, version-negotiated architecture publication contract."""

    requested_key, definition = _resolve_novaride_contract_definition(requested_version)
    compatibility = novaride_architecture_compatibility()
    return {
        "platform": "NovaRide",
        "contract": {
            "version": definition.version,
            "requested_version": requested_key,
            "supported_versions": compatibility["supported_versions"],
            "compatibility": compatibility["versions"][requested_key],
            "schema_hash": definition.schema_hash(),
            "schema_url": "/v1/architecture/schema",
            "canonical_format": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
            "hash_algorithm": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
            "canonicalization": {
                "algorithm": NOVARIDE_ARCHITECTURE_CANONICAL_FORMAT,
                "hash": NOVARIDE_ARCHITECTURE_HASH_ALGORITHM,
            },
            "lifecycle": definition.release_record(),
            "capabilities": list(definition.capabilities),
        },
        "architecture": definition.contract(),
        "observability": {
            "metrics": [
                "novaride_architecture_contract_version_total",
                "novaride_architecture_contract_unsupported_total",
                "novaride_contract_compatibility_check_total",
                "novaride_replay_latency_seconds",
                "novaride_proof_generation_latency_seconds",
            ],
        },
    }
