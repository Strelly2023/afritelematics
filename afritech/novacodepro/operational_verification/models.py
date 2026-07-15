from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .enums import CapabilityState, Decision, EvidenceStatus, VerificationDomain
from .hashing import domain_hash, utc_now, without_integrity_fields


def _list(value: tuple[str, ...] | list[str] | None = None) -> list[str]:
    return list(value or [])


@dataclass(slots=True)
class ExecutionEnvironment:
    id: str
    tenant_id: str
    organization_id: str
    project_id: str
    product_id: str
    release_id: str
    environment: str
    region: str
    version: str
    created_by: str
    correlation_id: str
    schema_version: str = "1.0"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)


@dataclass(slots=True)
class EvidenceReference:
    evidence_id: str
    evidence_type: str
    uri: str
    checksum: str = ""
    status: EvidenceStatus = EvidenceStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["status"] = self.status.value
        return body


@dataclass(slots=True)
class EvidenceEnvelope:
    evidence_id: str
    evidence_type: str
    producer: str
    producer_version: str
    environment: str
    subject: str
    release_id: str
    execution_id: str
    collected_at: str
    valid_from: str
    valid_until: str
    status: EvidenceStatus
    source_uri: str = ""
    artifact_refs: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    findings: list[dict[str, Any]] = field(default_factory=list)
    trace_ids: list[str] = field(default_factory=list)
    screenshot_refs: list[str] = field(default_factory=list)
    log_refs: list[str] = field(default_factory=list)
    checksum: str = ""
    signature: str = ""
    correlation_id: str = ""
    schema_version: str = "1.0"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["status"] = self.status.value
        if not body["checksum"]:
            body["checksum"] = domain_hash("novacodepro.evidence.checksum", without_integrity_fields(body))
        if not body["signature"]:
            assurance = self.metadata.get("signature_assurance", "DEVELOPMENT_ONLY")
            body["signature"] = domain_hash(f"novacodepro.evidence.signature.{assurance}", without_integrity_fields(body))
        return body


@dataclass(slots=True)
class VerificationCheck:
    id: str
    name: str
    domain: VerificationDomain
    status: CapabilityState = CapabilityState.CONFIGURED
    required: bool = True
    evidence_refs: list[str] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["domain"] = self.domain.value
        body["status"] = self.status.value
        return body


@dataclass(slots=True)
class CapabilityVerification:
    id: str
    tenant_id: str
    organization_id: str
    project_id: str
    product_id: str
    release_id: str
    environment: str
    region: str
    version: str
    status: CapabilityState
    created_by: str
    correlation_id: str
    domain: VerificationDomain
    checks: list[VerificationCheck] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    schema_version: str = "1.0"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    integrity_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["status"] = self.status.value
        body["domain"] = self.domain.value
        body["checks"] = [check.to_dict() for check in self.checks]
        body["integrity_hash"] = self.integrity_hash or domain_hash("novacodepro.capability", without_integrity_fields(body))
        return body


@dataclass(slots=True)
class OperationalVerificationProgram:
    id: str
    tenant_id: str
    organization_id: str
    project_id: str
    product_id: str
    release_id: str
    environment: str
    region: str
    version: str
    status: CapabilityState
    created_by: str
    correlation_id: str
    capabilities: list[CapabilityVerification] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    schema_version: str = "1.0"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    integrity_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["status"] = self.status.value
        body["capabilities"] = [capability.to_dict() for capability in self.capabilities]
        body["integrity_hash"] = self.integrity_hash or domain_hash("novacodepro.program", without_integrity_fields(body))
        return body


@dataclass(slots=True)
class OperationalVerificationRun:
    id: str
    program_id: str
    tenant_id: str
    organization_id: str
    project_id: str
    product_id: str
    release_id: str
    environment: str
    region: str
    version: str
    status: CapabilityState
    created_by: str
    correlation_id: str
    evidence_refs: list[str] = field(default_factory=list)
    schema_version: str = "1.0"
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    integrity_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["status"] = self.status.value
        body["integrity_hash"] = self.integrity_hash or domain_hash("novacodepro.run", without_integrity_fields(body))
        return body


@dataclass(slots=True)
class GovernanceDecision:
    id: str
    workflow_id: str
    release_id: str
    prr_id: str
    actor_id: str
    actor_type: str
    role: str
    decision: Decision
    reason: str
    evidence_refs: list[str]
    evidence_package_hash: str
    approval_scope: dict[str, Any]
    conflict_of_interest_checked: bool
    created_at: str = field(default_factory=utc_now)
    signature: str = ""

    def to_dict(self) -> dict[str, Any]:
        body = asdict(self)
        body["decision"] = self.decision.value
        body["signature"] = self.signature or domain_hash("novacodepro.approval", without_integrity_fields(body))
        return body
