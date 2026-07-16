"""Shared NovaTech enterprise data model and governed access registry.

The model keeps shared identity and reference data explicit while allowing each
product to own its own operational schema namespace, versioned data contracts,
and event definitions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Mapping


DEFAULT_MODEL_VERSION = "2026.07.0"
DEFAULT_CREATED_AT = "2026-07-16T00:00:00+00:00"


class EnterpriseDataGovernanceError(RuntimeError):
    """Raised when the enterprise data model breaks governance rules."""


class DataSharingLevel(str, Enum):
    PRIVATE = "PRIVATE"
    PRODUCT_GROUP = "PRODUCT_GROUP"
    ENTERPRISE = "ENTERPRISE"
    PARTNER = "PARTNER"
    PUBLIC = "PUBLIC"
    RESTRICTED = "RESTRICTED"
    REGULATED = "REGULATED"


class SchemaChangeClass(str, Enum):
    ADDITIVE = "ADDITIVE"
    COMPATIBLE = "COMPATIBLE"
    DEPRECATED = "DEPRECATED"
    BREAKING = "BREAKING"


class DataDomainStatus(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    RETIRED = "RETIRED"


class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    REVIEWED = "REVIEWED"
    APPROVED = "APPROVED"
    PUBLISHED = "PUBLISHED"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class SharedEnterpriseEntity:
    """Canonical shared entity owned by the enterprise core."""

    name: str
    source_of_truth: str
    fields: tuple[str, ...]
    classification: str
    sharing_level: DataSharingLevel = DataSharingLevel.ENTERPRISE
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise EnterpriseDataGovernanceError("shared entity name is required")
        if not self.source_of_truth.strip():
            raise EnterpriseDataGovernanceError("shared entity source_of_truth is required")
        if not self.fields:
            raise EnterpriseDataGovernanceError("shared entity fields are required")
        if len(set(self.fields)) != len(self.fields):
            raise EnterpriseDataGovernanceError("shared entity fields must be unique")
        if not self.classification.strip():
            raise EnterpriseDataGovernanceError("shared entity classification is required")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "source_of_truth": self.source_of_truth,
            "fields": list(self.fields),
            "classification": self.classification,
            "sharing_level": self.sharing_level.value,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class ProductDataExtension:
    """Product-owned extension table for a shared enterprise entity."""

    product_code: str
    base_entity: str
    table_name: str
    fields: tuple[str, ...]
    owner: str
    classification: str = "INTERNAL"

    def __post_init__(self) -> None:
        if not self.product_code.strip():
            raise EnterpriseDataGovernanceError("product_code is required")
        if not self.base_entity.strip():
            raise EnterpriseDataGovernanceError("base_entity is required")
        if not self.table_name.strip():
            raise EnterpriseDataGovernanceError("table_name is required")
        if not self.fields:
            raise EnterpriseDataGovernanceError("extension fields are required")
        if len(set(self.fields)) != len(self.fields):
            raise EnterpriseDataGovernanceError("extension fields must be unique")
        if not self.owner.strip():
            raise EnterpriseDataGovernanceError("extension owner is required")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "product_code": self.product_code,
            "base_entity": self.base_entity,
            "table_name": self.table_name,
            "fields": list(self.fields),
            "owner": self.owner,
            "classification": self.classification,
        }


@dataclass(frozen=True, slots=True)
class DataDomainRegistryEntry:
    """Product data domain record used for governed discovery and sharing."""

    id: str
    product_code: str
    name: str
    owner: str
    schema_name: str
    version: str
    status: DataDomainStatus
    classification: str
    region: str
    created_at: str

    def __post_init__(self) -> None:
        for field_name in (
            "id",
            "product_code",
            "name",
            "owner",
            "schema_name",
            "version",
            "classification",
            "region",
            "created_at",
        ):
            if not getattr(self, field_name).strip():
                raise EnterpriseDataGovernanceError(f"{field_name} is required")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "product_code": self.product_code,
            "name": self.name,
            "owner": self.owner,
            "schema_name": self.schema_name,
            "version": self.version,
            "status": self.status.value,
            "classification": self.classification,
            "region": self.region,
            "created_at": self.created_at,
        }


@dataclass(frozen=True, slots=True)
class DataContract:
    """Versioned governed access contract between two product domains."""

    contract_id: str
    producer_product: str
    consumer_product: str
    data_type: str
    schema_version: int
    purpose: str
    allowed_fields: tuple[str, ...]
    retention_policy: str
    consent_required: bool
    status: ContractStatus
    sharing_level: DataSharingLevel = DataSharingLevel.ENTERPRISE
    schema_change: SchemaChangeClass = SchemaChangeClass.COMPATIBLE
    classification: str = "CONFIDENTIAL"
    topic: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "contract_id",
            "producer_product",
            "consumer_product",
            "data_type",
            "purpose",
            "retention_policy",
            "classification",
        ):
            if not getattr(self, field_name).strip():
                raise EnterpriseDataGovernanceError(f"{field_name} is required")
        if self.schema_version < 1:
            raise EnterpriseDataGovernanceError("schema_version must be >= 1")
        if not self.allowed_fields:
            raise EnterpriseDataGovernanceError("allowed_fields are required")
        if len(set(self.allowed_fields)) != len(self.allowed_fields):
            raise EnterpriseDataGovernanceError("allowed_fields must be unique")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "producer_product": self.producer_product,
            "consumer_product": self.consumer_product,
            "data_type": self.data_type,
            "schema_version": self.schema_version,
            "purpose": self.purpose,
            "allowed_fields": list(self.allowed_fields),
            "retention_policy": self.retention_policy,
            "consent_required": self.consent_required,
            "status": self.status.value,
            "sharing_level": self.sharing_level.value,
            "schema_change": self.schema_change.value,
            "classification": self.classification,
            "topic": self.topic,
        }


@dataclass(frozen=True, slots=True)
class DataEventDefinition:
    """Registry entry for a governed, versioned domain event."""

    event_type: str
    event_version: int
    producer_product: str
    topic: str
    payload_fields: tuple[str, ...]
    consumers: tuple[str, ...]
    classification: str
    sharing_level: DataSharingLevel = DataSharingLevel.ENTERPRISE
    schema_change: SchemaChangeClass = SchemaChangeClass.COMPATIBLE
    retention_policy: str = "AUDIT"

    def __post_init__(self) -> None:
        if not self.event_type.strip():
            raise EnterpriseDataGovernanceError("event_type is required")
        if self.event_version < 1:
            raise EnterpriseDataGovernanceError("event_version must be >= 1")
        if not self.producer_product.strip():
            raise EnterpriseDataGovernanceError("producer_product is required")
        if not self.topic.strip():
            raise EnterpriseDataGovernanceError("topic is required")
        if not self.payload_fields:
            raise EnterpriseDataGovernanceError("payload_fields are required")
        if len(set(self.payload_fields)) != len(self.payload_fields):
            raise EnterpriseDataGovernanceError("payload_fields must be unique")
        if not self.consumers:
            raise EnterpriseDataGovernanceError("consumers are required")
        if len(set(self.consumers)) != len(self.consumers):
            raise EnterpriseDataGovernanceError("consumers must be unique")
        if not self.classification.strip():
            raise EnterpriseDataGovernanceError("classification is required")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_version": self.event_version,
            "producer_product": self.producer_product,
            "topic": self.topic,
            "payload_fields": list(self.payload_fields),
            "consumers": list(self.consumers),
            "classification": self.classification,
            "sharing_level": self.sharing_level.value,
            "schema_change": self.schema_change.value,
            "retention_policy": self.retention_policy,
        }


@dataclass(frozen=True, slots=True)
class DomainEventEnvelope:
    """Standard event envelope for governed cross-product synchronization."""

    event_id: str
    event_type: str
    event_version: int
    producer_product: str
    tenant_id: str
    organization_id: str
    subject_id: str
    occurred_at: str
    correlation_id: str
    classification: str
    payload: Mapping[str, Any]
    region: str = "GLOBAL"
    causation_id: str = ""
    schema_version: str = "1"

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "event_type",
            "producer_product",
            "tenant_id",
            "organization_id",
            "subject_id",
            "occurred_at",
            "correlation_id",
            "classification",
            "region",
            "schema_version",
        ):
            if not getattr(self, field_name).strip():
                raise EnterpriseDataGovernanceError(f"{field_name} is required")
        if self.event_version < 1:
            raise EnterpriseDataGovernanceError("event_version must be >= 1")
        if not isinstance(self.payload, Mapping):
            raise EnterpriseDataGovernanceError("payload must be a mapping")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "producer_product": self.producer_product,
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "subject_id": self.subject_id,
            "occurred_at": self.occurred_at,
            "correlation_id": self.correlation_id,
            "classification": self.classification,
            "payload": dict(self.payload),
            "region": self.region,
            "causation_id": self.causation_id,
            "schema_version": self.schema_version,
            "evidence_hash": self.evidence_hash,
        }

    @property
    def evidence_hash(self) -> str:
        canonical = json.dumps(self._hashable_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
        return f"sha256:{hashlib.sha256(canonical).hexdigest()}"

    def _hashable_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "event_version": self.event_version,
            "producer_product": self.producer_product,
            "tenant_id": self.tenant_id,
            "organization_id": self.organization_id,
            "subject_id": self.subject_id,
            "occurred_at": self.occurred_at,
            "correlation_id": self.correlation_id,
            "classification": self.classification,
            "payload": _normalize_value(self.payload),
            "region": self.region,
            "causation_id": self.causation_id,
            "schema_version": self.schema_version,
        }


DataEventEnvelope = DomainEventEnvelope


@dataclass(frozen=True, slots=True)
class EnterpriseDataModel:
    """Immutable registry of shared enterprise data and product data domains."""

    shared_entities: tuple[SharedEnterpriseEntity, ...]
    product_domains: tuple[DataDomainRegistryEntry, ...]
    product_extensions: tuple[ProductDataExtension, ...]
    contracts: tuple[DataContract, ...]
    events: tuple[DataEventDefinition, ...]
    version: str = DEFAULT_MODEL_VERSION
    generated_at: str = DEFAULT_CREATED_AT

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise EnterpriseDataGovernanceError("version is required")
        if not self.generated_at.strip():
            raise EnterpriseDataGovernanceError("generated_at is required")

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "platform": "NovaTech",
            "version": self.version,
            "generated_at": self.generated_at,
            "shared_entities": [item.canonical_dict() for item in self.shared_entities],
            "product_domains": [item.canonical_dict() for item in self.product_domains],
            "product_extensions": [item.canonical_dict() for item in self.product_extensions],
            "contracts": [item.canonical_dict() for item in self.contracts],
            "events": [item.canonical_dict() for item in self.events],
            "sharing_levels": [item.value for item in DataSharingLevel],
            "schema_change_classes": [item.value for item in SchemaChangeClass],
        }

    def summary(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "shared_entity_count": len(self.shared_entities),
            "product_domain_count": len(self.product_domains),
            "product_extension_count": len(self.product_extensions),
            "contract_count": len(self.contracts),
            "event_count": len(self.events),
            "shared_sources": sorted({entity.source_of_truth for entity in self.shared_entities}),
        }

    def shared_entity(self, name: str) -> SharedEnterpriseEntity:
        normalized = name.strip().lower()
        for entity in self.shared_entities:
            if entity.name.lower() == normalized:
                return entity
        raise EnterpriseDataGovernanceError(f"unknown shared entity: {name}")

    def product_domain(self, product_code: str) -> DataDomainRegistryEntry:
        normalized = product_code.strip().lower()
        for domain in self.product_domains:
            if domain.product_code.lower() == normalized:
                return domain
        raise EnterpriseDataGovernanceError(f"unknown product domain: {product_code}")

    def product_extension(self, product_code: str, base_entity: str) -> ProductDataExtension:
        normalized_product = product_code.strip().lower()
        normalized_entity = base_entity.strip().lower()
        for extension in self.product_extensions:
            if (
                extension.product_code.lower() == normalized_product
                and extension.base_entity.lower() == normalized_entity
            ):
                return extension
        raise EnterpriseDataGovernanceError(
            f"unknown product extension: {product_code}:{base_entity}"
        )

    def contract(self, contract_id: str) -> DataContract:
        normalized = contract_id.strip().lower()
        for contract in self.contracts:
            if contract.contract_id.lower() == normalized:
                return contract
        raise EnterpriseDataGovernanceError(f"unknown data contract: {contract_id}")

    def event(self, event_type: str) -> DataEventDefinition:
        normalized = event_type.strip().lower()
        for event in self.events:
            if event.event_type.lower() == normalized:
                return event
        raise EnterpriseDataGovernanceError(f"unknown data event: {event_type}")

    def allowed_fields(self, contract_id: str) -> tuple[str, ...]:
        return self.contract(contract_id).allowed_fields

    def project_payload(self, contract_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        contract = self.contract(contract_id)
        projected = {field: payload[field] for field in contract.allowed_fields if field in payload}
        return projected

    def register_product_domain(
        self,
        domain: DataDomainRegistryEntry,
        *,
        extensions: tuple[ProductDataExtension, ...] = (),
        contracts: tuple[DataContract, ...] = (),
        events: tuple[DataEventDefinition, ...] = (),
    ) -> "EnterpriseDataModel":
        return EnterpriseDataModel(
            shared_entities=self.shared_entities,
            product_domains=_replace_unique(self.product_domains, domain, key=lambda item: item.product_code),
            product_extensions=_replace_many(self.product_extensions, extensions, key=lambda item: (item.product_code, item.base_entity)),
            contracts=_replace_many(self.contracts, contracts, key=lambda item: item.contract_id),
            events=_replace_many(self.events, events, key=lambda item: item.event_type),
            version=self.version,
            generated_at=self.generated_at,
        )

    def with_contract(self, contract: DataContract) -> "EnterpriseDataModel":
        return EnterpriseDataModel(
            shared_entities=self.shared_entities,
            product_domains=self.product_domains,
            product_extensions=self.product_extensions,
            contracts=_replace_unique(self.contracts, contract, key=lambda item: item.contract_id),
            events=self.events,
            version=self.version,
            generated_at=self.generated_at,
        )

    def with_event(self, event: DataEventDefinition) -> "EnterpriseDataModel":
        return EnterpriseDataModel(
            shared_entities=self.shared_entities,
            product_domains=self.product_domains,
            product_extensions=self.product_extensions,
            contracts=self.contracts,
            events=_replace_unique(self.events, event, key=lambda item: item.event_type),
            version=self.version,
            generated_at=self.generated_at,
        )


def default_enterprise_data_model() -> EnterpriseDataModel:
    shared_entities = (
        SharedEnterpriseEntity(
            name="Organization",
            source_of_truth="novaid",
            fields=("id", "tenant_id", "organization_id", "name", "status", "classification"),
            classification="RESTRICTED",
            description="Enterprise organization record shared across products.",
        ),
        SharedEnterpriseEntity(
            name="Tenant",
            source_of_truth="novaid",
            fields=("id", "tenant_id", "name", "status", "region", "classification"),
            classification="RESTRICTED",
            description="Tenant-scoped identity and policy boundary.",
        ),
        SharedEnterpriseEntity(
            name="Person",
            source_of_truth="novaid",
            fields=("id", "tenant_id", "organization_id", "legal_name", "display_name", "status"),
            classification="RESTRICTED",
            description="Canonical person identity reused across products.",
        ),
        SharedEnterpriseEntity(
            name="UserAccount",
            source_of_truth="novaid",
            fields=("id", "person_id", "tenant_id", "role", "status", "last_login_at"),
            classification="RESTRICTED",
            description="Authenticated account bound to a person.",
        ),
        SharedEnterpriseEntity(
            name="Identity",
            source_of_truth="novaid",
            fields=("id", "person_id", "verification_status", "country", "verified_at", "source"),
            classification="RESTRICTED",
            description="Verified identity projection used by downstream products.",
        ),
        SharedEnterpriseEntity(
            name="Role",
            source_of_truth="novapolicy",
            fields=("id", "name", "status", "scope", "tenant_id"),
            classification="INTERNAL",
            description="Governed role definition.",
        ),
        SharedEnterpriseEntity(
            name="Permission",
            source_of_truth="novapolicy",
            fields=("id", "name", "resource", "action", "status"),
            classification="INTERNAL",
            description="Governed permission definition.",
        ),
        SharedEnterpriseEntity(
            name="Address",
            source_of_truth="novacore",
            fields=("id", "person_id", "line1", "line2", "city", "region", "country_code", "postal_code"),
            classification="INTERNAL",
            description="Reference address record.",
        ),
        SharedEnterpriseEntity(
            name="Location",
            source_of_truth="novacore",
            fields=("id", "label", "latitude", "longitude", "country_code", "region"),
            classification="INTERNAL",
            description="Reference geolocation record.",
        ),
        SharedEnterpriseEntity(
            name="Country",
            source_of_truth="novacore",
            fields=("code", "name", "region", "currency_code", "languages"),
            classification="PUBLIC",
            description="Shared country reference data.",
        ),
        SharedEnterpriseEntity(
            name="Currency",
            source_of_truth="novacore",
            fields=("code", "name", "symbol", "minor_unit", "country_codes"),
            classification="PUBLIC",
            description="Shared currency reference data.",
        ),
        SharedEnterpriseEntity(
            name="Language",
            source_of_truth="novacore",
            fields=("code", "name", "script", "direction"),
            classification="PUBLIC",
            description="Shared language reference data.",
        ),
        SharedEnterpriseEntity(
            name="Device",
            source_of_truth="novaid",
            fields=("id", "person_id", "tenant_id", "device_type", "trust_state", "last_seen_at"),
            classification="RESTRICTED",
            description="Bound device identity and trust record.",
        ),
        SharedEnterpriseEntity(
            name="ContactMethod",
            source_of_truth="novaid",
            fields=("id", "person_id", "kind", "value_masked", "verified", "primary"),
            classification="CONFIDENTIAL",
            description="Canonical contact method reused across products.",
        ),
        SharedEnterpriseEntity(
            name="Document",
            source_of_truth="novacore",
            fields=("id", "tenant_id", "owner_id", "document_type", "classification", "version"),
            classification="CONFIDENTIAL",
            description="Shared document metadata record.",
        ),
        SharedEnterpriseEntity(
            name="Consent",
            source_of_truth="novaconsent",
            fields=("id", "person_id", "purpose", "scope", "status", "recorded_at"),
            classification="REGULATED",
            description="Consent registry record.",
        ),
        SharedEnterpriseEntity(
            name="Policy",
            source_of_truth="novapolicy",
            fields=("id", "policy_key", "version", "status", "scope", "effective_at"),
            classification="INTERNAL",
            description="Enterprise policy record.",
        ),
        SharedEnterpriseEntity(
            name="AuditEvent",
            source_of_truth="novaaudit",
            fields=("id", "tenant_id", "actor_id", "action", "resource", "recorded_at"),
            classification="RESTRICTED",
            description="Immutable audit record.",
        ),
        SharedEnterpriseEntity(
            name="Evidence",
            source_of_truth="novaaudit",
            fields=("id", "tenant_id", "artifact_id", "hash", "recorded_at", "status"),
            classification="RESTRICTED",
            description="Immutable evidence record.",
        ),
    )

    product_domains = (
        DataDomainRegistryEntry(
            id="domain_identity_v1",
            product_code="novaid",
            name="NovaID Identity",
            owner="NovaID Identity Team",
            schema_name="identity",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="RESTRICTED",
            region="GLOBAL",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_consent_v1",
            product_code="novaconsent",
            name="NovaConsent Consent",
            owner="NovaConsent Governance Team",
            schema_name="consent",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="REGULATED",
            region="GLOBAL",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_policy_v1",
            product_code="novapolicy",
            name="NovaPolicy Policy",
            owner="NovaPolicy Governance Team",
            schema_name="governance",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="INTERNAL",
            region="GLOBAL",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_audit_v1",
            product_code="novaaudit",
            name="NovaAudit Audit",
            owner="NovaAudit Evidence Team",
            schema_name="audit",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="RESTRICTED",
            region="GLOBAL",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_core_v1",
            product_code="novacore",
            name="NovaCore Reference Data",
            owner="NovaCore Reference Data Team",
            schema_name="core",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="PUBLIC",
            region="GLOBAL",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_novaride_v1",
            product_code="novaride",
            name="NovaRide Mobility",
            owner="NovaRide Platform Team",
            schema_name="novaride",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="CONFIDENTIAL",
            region="MULTI_REGION",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_novapay_v1",
            product_code="novapay",
            name="NovaPay Payments",
            owner="NovaPay Platform Team",
            schema_name="novapay",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="RESTRICTED",
            region="MULTI_REGION",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_novahealth_v1",
            product_code="novahealth",
            name="NovaHealth Clinical",
            owner="NovaHealth Platform Team",
            schema_name="novahealth",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.PLANNED,
            classification="REGULATED",
            region="MULTI_REGION",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_novacommerce_v1",
            product_code="novacommerce",
            name="NovaCommerce Commerce",
            owner="NovaCommerce Platform Team",
            schema_name="novacommerce",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.PLANNED,
            classification="CONFIDENTIAL",
            region="MULTI_REGION",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_novalogistics_v1",
            product_code="novalogistics",
            name="NovaLogistics Operations",
            owner="NovaLogistics Platform Team",
            schema_name="novalogistics",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.PLANNED,
            classification="CONFIDENTIAL",
            region="MULTI_REGION",
            created_at=DEFAULT_CREATED_AT,
        ),
        DataDomainRegistryEntry(
            id="domain_novacodepro_v1",
            product_code="novacodepro",
            name="NovaCodePro Solution Engineering",
            owner="NovaCodePro Platform Team",
            schema_name="novacodepro",
            version=DEFAULT_MODEL_VERSION,
            status=DataDomainStatus.ACTIVE,
            classification="CONFIDENTIAL",
            region="MULTI_REGION",
            created_at=DEFAULT_CREATED_AT,
        ),
    )

    product_extensions = (
        ProductDataExtension(
            product_code="novaride",
            base_entity="Person",
            table_name="novaride.driver_profile",
            fields=("person_id", "driver_license_number", "driver_status", "rating", "safety_score"),
            owner="NovaRide Platform Team",
            classification="RESTRICTED",
        ),
        ProductDataExtension(
            product_code="novapay",
            base_entity="Person",
            table_name="novapay.customer_profile",
            fields=("person_id", "kyc_level", "transfer_limit", "risk_rating", "wallet_status"),
            owner="NovaPay Platform Team",
            classification="RESTRICTED",
        ),
        ProductDataExtension(
            product_code="novahealth",
            base_entity="Person",
            table_name="novahealth.patient_profile",
            fields=("person_id", "patient_number", "healthcare_identifier", "record_status"),
            owner="NovaHealth Platform Team",
            classification="REGULATED",
        ),
        ProductDataExtension(
            product_code="novacommerce",
            base_entity="Person",
            table_name="novacommerce.merchant_profile",
            fields=("person_id", "merchant_number", "merchant_status", "risk_class"),
            owner="NovaCommerce Platform Team",
            classification="CONFIDENTIAL",
        ),
        ProductDataExtension(
            product_code="novacodepro",
            base_entity="Person",
            table_name="novacodepro.workspace_profile",
            fields=("person_id", "workspace_id", "workspace_mode", "approval_profile"),
            owner="NovaCodePro Platform Team",
            classification="CONFIDENTIAL",
        ),
    )

    contracts = (
        DataContract(
            contract_id="identity_verified_to_novaride",
            producer_product="novaid",
            consumer_product="novaride",
            data_type="VerifiedIdentity",
            schema_version=1,
            purpose="driver_onboarding",
            allowed_fields=("person_id", "verification_status", "legal_name", "date_of_birth_verified", "country"),
            retention_policy="OPERATIONAL",
            consent_required=True,
            status=ContractStatus.APPROVED,
            sharing_level=DataSharingLevel.ENTERPRISE,
            classification="RESTRICTED",
            topic="novatech.identity.events",
        ),
        DataContract(
            contract_id="identity_verified_to_novapay",
            producer_product="novaid",
            consumer_product="novapay",
            data_type="VerifiedIdentity",
            schema_version=1,
            purpose="kyc_assurance",
            allowed_fields=("person_id", "verification_status", "legal_name", "country", "verified_at"),
            retention_policy="AUDIT",
            consent_required=True,
            status=ContractStatus.APPROVED,
            sharing_level=DataSharingLevel.ENTERPRISE,
            classification="RESTRICTED",
            topic="novatech.identity.events",
        ),
        DataContract(
            contract_id="identity_verified_to_novahealth",
            producer_product="novaid",
            consumer_product="novahealth",
            data_type="VerifiedIdentity",
            schema_version=1,
            purpose="patient_identity_verification",
            allowed_fields=("person_id", "verification_status", "legal_name", "country"),
            retention_policy="OPERATIONAL",
            consent_required=True,
            status=ContractStatus.APPROVED,
            sharing_level=DataSharingLevel.REGULATED,
            classification="REGULATED",
            topic="novatech.identity.events",
        ),
        DataContract(
            contract_id="policy_decision_to_novacodepro",
            producer_product="novapolicy",
            consumer_product="novacodepro",
            data_type="PolicyDecision",
            schema_version=1,
            purpose="governed_execution",
            allowed_fields=("policy_id", "policy_version", "decision", "reason", "approver"),
            retention_policy="AUDIT",
            consent_required=False,
            status=ContractStatus.APPROVED,
            sharing_level=DataSharingLevel.ENTERPRISE,
            classification="INTERNAL",
            topic="novatech.governance.events",
        ),
        DataContract(
            contract_id="audit_evidence_to_novacodepro",
            producer_product="novaaudit",
            consumer_product="novacodepro",
            data_type="EvidenceReference",
            schema_version=1,
            purpose="project_traceability",
            allowed_fields=("evidence_id", "artifact_id", "hash", "recorded_at", "status"),
            retention_policy="AUDIT",
            consent_required=False,
            status=ContractStatus.APPROVED,
            sharing_level=DataSharingLevel.RESTRICTED,
            classification="RESTRICTED",
            topic="novatech.audit.events",
        ),
        DataContract(
            contract_id="consent_withdrawn_to_novapay",
            producer_product="novaconsent",
            consumer_product="novapay",
            data_type="ConsentStatus",
            schema_version=1,
            purpose="compliance_eligibility",
            allowed_fields=("person_id", "purpose", "scope", "status", "recorded_at"),
            retention_policy="AUDIT",
            consent_required=False,
            status=ContractStatus.APPROVED,
            sharing_level=DataSharingLevel.REGULATED,
            classification="REGULATED",
            topic="novatech.consent.events",
        ),
    )

    events = (
        DataEventDefinition(
            event_type="identity.verified.v1",
            event_version=1,
            producer_product="novaid",
            topic="novatech.identity.events",
            payload_fields=("person_id", "verification_status", "legal_name", "country", "verified_at"),
            consumers=("novaride", "novapay", "novahealth"),
            classification="RESTRICTED",
            sharing_level=DataSharingLevel.ENTERPRISE,
        ),
        DataEventDefinition(
            event_type="ride.requested.v1",
            event_version=1,
            producer_product="novaride",
            topic="novatech.mobility.events",
            payload_fields=("ride_id", "passenger_id", "pickup_location", "destination_location", "requested_at"),
            consumers=("novapay", "novacodepro"),
            classification="CONFIDENTIAL",
            sharing_level=DataSharingLevel.ENTERPRISE,
        ),
        DataEventDefinition(
            event_type="wallet.created.v1",
            event_version=1,
            producer_product="novapay",
            topic="novatech.payments.events",
            payload_fields=("wallet_id", "person_id", "currency", "status", "created_at"),
            consumers=("novacodepro", "novaride"),
            classification="RESTRICTED",
            sharing_level=DataSharingLevel.ENTERPRISE,
        ),
        DataEventDefinition(
            event_type="consent.withdrawn.v1",
            event_version=1,
            producer_product="novaconsent",
            topic="novatech.consent.events",
            payload_fields=("person_id", "purpose", "scope", "status", "recorded_at"),
            consumers=("novaid", "novapay", "novaride", "novahealth"),
            classification="REGULATED",
            sharing_level=DataSharingLevel.REGULATED,
        ),
        DataEventDefinition(
            event_type="audit.recorded.v1",
            event_version=1,
            producer_product="novaaudit",
            topic="novatech.audit.events",
            payload_fields=("audit_id", "tenant_id", "actor_id", "action", "recorded_at"),
            consumers=("novacodepro", "novaride", "novapay"),
            classification="RESTRICTED",
            sharing_level=DataSharingLevel.RESTRICTED,
        ),
    )

    return EnterpriseDataModel(
        shared_entities=shared_entities,
        product_domains=product_domains,
        product_extensions=product_extensions,
        contracts=contracts,
        events=events,
    )


def validate_enterprise_data_model(model: EnterpriseDataModel | None = None) -> bool:
    current = model or default_enterprise_data_model()
    required_shared_entities = {
        "Organization",
        "Tenant",
        "Person",
        "UserAccount",
        "Identity",
        "Role",
        "Permission",
        "Address",
        "Location",
        "Country",
        "Currency",
        "Language",
        "Device",
        "ContactMethod",
        "Document",
        "Consent",
        "Policy",
        "AuditEvent",
        "Evidence",
    }
    observed_shared = {entity.name for entity in current.shared_entities}
    missing = required_shared_entities - observed_shared
    if missing:
        raise EnterpriseDataGovernanceError(
            "missing shared enterprise entities: " + ", ".join(sorted(missing))
        )

    required_products = {
        "novaid",
        "novaconsent",
        "novapolicy",
        "novaaudit",
        "novacore",
        "novaride",
        "novapay",
        "novahealth",
        "novacommerce",
        "novalogistics",
        "novacodepro",
    }
    observed_products = {domain.product_code for domain in current.product_domains}
    missing_products = required_products - observed_products
    if missing_products:
        raise EnterpriseDataGovernanceError(
            "missing product domains: " + ", ".join(sorted(missing_products))
        )

    if "novaid" != current.shared_entity("Identity").source_of_truth:
        raise EnterpriseDataGovernanceError("identity source of truth must be novaid")
    if "novaconsent" != current.shared_entity("Consent").source_of_truth:
        raise EnterpriseDataGovernanceError("consent source of truth must be novaconsent")
    if "novaaudit" != current.shared_entity("AuditEvent").source_of_truth:
        raise EnterpriseDataGovernanceError("audit source of truth must be novaaudit")
    if "novaaudit" != current.shared_entity("Evidence").source_of_truth:
        raise EnterpriseDataGovernanceError("evidence source of truth must be novaaudit")

    for contract in current.contracts:
        if contract.status not in {ContractStatus.APPROVED, ContractStatus.PUBLISHED}:
            raise EnterpriseDataGovernanceError(
                f"contract must be approved or published: {contract.contract_id}"
            )
        if contract.producer_product not in observed_products:
            raise EnterpriseDataGovernanceError(
                f"unknown contract producer: {contract.contract_id}"
            )
        if contract.consumer_product not in observed_products:
            raise EnterpriseDataGovernanceError(
                f"unknown contract consumer: {contract.contract_id}"
            )
    for event in current.events:
        if event.producer_product not in observed_products:
            raise EnterpriseDataGovernanceError(f"unknown event producer: {event.event_type}")
        if not set(event.consumers).issubset(observed_products):
            raise EnterpriseDataGovernanceError(f"unknown event consumer for {event.event_type}")
    return True


def enterprise_data_manifest(model: EnterpriseDataModel | None = None) -> dict[str, Any]:
    current = model or default_enterprise_data_model()
    manifest = current.canonical_dict()
    manifest["summary"] = current.summary()
    manifest["validation"] = {
        "status": "PASS" if validate_enterprise_data_model(current) else "FAIL",
        "rules": [
            "share meaning, not tables",
            "share contracts, not unrestricted access",
            "share events, not direct writes",
            "reuse identity, not duplicated users",
            "allow extension, not uncontrolled schema changes",
        ],
    }
    return manifest


def _normalize_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _normalize_value(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, tuple):
        return [_normalize_value(item) for item in value]
    if isinstance(value, list):
        return [_normalize_value(item) for item in value]
    return value


def _replace_unique(items: tuple[Any, ...], item: Any, *, key) -> tuple[Any, ...]:
    existing = [value for value in items if key(value) != key(item)]
    existing.append(item)
    return tuple(existing)


def _replace_many(items: tuple[Any, ...], replacements: tuple[Any, ...], *, key) -> tuple[Any, ...]:
    updated = list(items)
    for replacement in replacements:
        updated = [value for value in updated if key(value) != key(replacement)]
        updated.append(replacement)
    return tuple(updated)


@dataclass(frozen=True, slots=True)
class EnterpriseDataGateway:
    """Read-only governed access layer over the shared enterprise data model."""

    model: EnterpriseDataModel = field(default_factory=default_enterprise_data_model)

    def summary(self) -> dict[str, Any]:
        return self.model.summary()

    def manifest(self) -> dict[str, Any]:
        return enterprise_data_manifest(self.model)

    def list_shared_entities(self) -> tuple[dict[str, Any], ...]:
        return tuple(entity.canonical_dict() for entity in self.model.shared_entities)

    def get_shared_entity(self, name: str) -> dict[str, Any]:
        return self.model.shared_entity(name).canonical_dict()

    def list_product_domains(self) -> tuple[dict[str, Any], ...]:
        return tuple(domain.canonical_dict() for domain in self.model.product_domains)

    def get_product_domain(self, product_code: str) -> dict[str, Any]:
        return self.model.product_domain(product_code).canonical_dict()

    def list_product_extensions(self) -> tuple[dict[str, Any], ...]:
        return tuple(extension.canonical_dict() for extension in self.model.product_extensions)

    def get_product_extension(self, product_code: str, base_entity: str) -> dict[str, Any]:
        return self.model.product_extension(product_code, base_entity).canonical_dict()

    def list_contracts(self) -> tuple[dict[str, Any], ...]:
        return tuple(contract.canonical_dict() for contract in self.model.contracts)

    def get_contract(self, contract_id: str) -> dict[str, Any]:
        return self.model.contract(contract_id).canonical_dict()

    def list_events(self) -> tuple[dict[str, Any], ...]:
        return tuple(event.canonical_dict() for event in self.model.events)

    def get_event(self, event_type: str) -> dict[str, Any]:
        return self.model.event(event_type).canonical_dict()

    def project_contract_payload(self, contract_id: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return self.model.project_payload(contract_id, payload)

    def authorize_projection(self, contract_id: str, consumer_product: str, purpose: str) -> dict[str, Any]:
        contract = self.model.contract(contract_id)
        if contract.status not in {ContractStatus.APPROVED, ContractStatus.PUBLISHED}:
            raise EnterpriseDataGovernanceError("contract is not approved")
        if contract.consumer_product != consumer_product:
            raise EnterpriseDataGovernanceError("contract consumer mismatch")
        if contract.purpose != purpose:
            raise EnterpriseDataGovernanceError("contract purpose mismatch")
        return contract.canonical_dict()


__all__ = [
    "ContractStatus",
    "DataContract",
    "DataDomainRegistryEntry",
    "DataDomainStatus",
    "DataEventDefinition",
    "DataEventEnvelope",
    "DataSharingLevel",
    "DEFAULT_CREATED_AT",
    "DEFAULT_MODEL_VERSION",
    "EnterpriseDataGateway",
    "EnterpriseDataGovernanceError",
    "EnterpriseDataModel",
    "ProductDataExtension",
    "SchemaChangeClass",
    "SharedEnterpriseEntity",
    "default_enterprise_data_model",
    "enterprise_data_manifest",
    "validate_enterprise_data_model",
]
