"""Machine-verifiable NovaTech platform contracts."""

from afritech.platform_contracts.runtime import (
    ApiLifecycle,
    CapabilityLayer,
    ProductLifecycle,
    TrustAssessment,
    TrustLevel,
    VersionVector,
    assess_trust_level,
    validate_capability_dependencies,
)
from afritech.platform_contracts.registry import (
    architecture_metrics,
    capability_graph,
    negotiate_version,
    schema_registry_manifest,
    validate_contract_payload,
)
from afritech.platform_contracts.schema_registry import (
    CompatibilityReport,
    EVENT_REGISTRY_ID,
    EVENT_REGISTRY_PATH,
    EVENT_SCHEMA_OUTPUT_DIR,
    SchemaRegistry,
    SchemaRegistryEntry,
    SchemaRegistryError,
    build_schema_catalog,
    build_schema_registry,
)

__all__ = [
    "ApiLifecycle",
    "CapabilityLayer",
    "ProductLifecycle",
    "TrustAssessment",
    "TrustLevel",
    "VersionVector",
    "assess_trust_level",
    "validate_capability_dependencies",
    "architecture_metrics",
    "capability_graph",
    "negotiate_version",
    "schema_registry_manifest",
    "validate_contract_payload",
    "CompatibilityReport",
    "EVENT_REGISTRY_ID",
    "EVENT_REGISTRY_PATH",
    "EVENT_SCHEMA_OUTPUT_DIR",
    "SchemaRegistry",
    "SchemaRegistryEntry",
    "SchemaRegistryError",
    "build_schema_catalog",
    "build_schema_registry",
]
