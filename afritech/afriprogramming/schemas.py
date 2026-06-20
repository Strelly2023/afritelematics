from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StudioGenerateCodeRequest(BaseModel):
    prompt: str = Field(..., min_length=3)
    mode: str = Field(default="code")
    project_id: str = Field(default="project-employee-rbac")


class StudioExplainCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    context: str = ""


class StudioAnalyzeRepoRequest(BaseModel):
    project_id: str = Field(default="project-employee-rbac")
    focus: str = ""


class CloudRequestDeployRequest(BaseModel):
    service: str = Field(..., min_length=1)
    environment: str = Field(default="staging")
    image: str = Field(default="nova-programming:latest")
    rationale: str = ""


class CloudDeployRequest(BaseModel):
    request_id: str = Field(..., min_length=1)


class CloudScaleRequest(BaseModel):
    service: str = Field(..., min_length=1)
    replicas: int = Field(default=1, ge=1)


class GovernancePolicyRequest(BaseModel):
    policy_name: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    description: str = ""


class GovernanceCheckRequest(BaseModel):
    policy_name: str = Field(default="default-policy")
    target: str = Field(..., min_length=1)


class GovernanceApproveRequest(BaseModel):
    request_id: str = Field(..., min_length=1)
    decision: str = Field(default="approved")
    notes: str = ""


class PolicyCreateRequest(BaseModel):
    policy_name: str = Field(..., min_length=1)
    version: str = Field(default="v1", min_length=1)
    rule_type: str = Field(..., min_length=1)
    rule_payload: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class PolicyEvaluateRequest(BaseModel):
    action: str = Field(..., min_length=1)
    target: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class AssuranceRunRequest(BaseModel):
    actor_user_id: str = Field(default="system", min_length=1)


class RetentionSetRequest(BaseModel):
    record_type: str = Field(..., min_length=1)
    retention_days: int = Field(default=0, ge=0)
    legal_hold: bool = True
    deletion_allowed: bool = False


class AssuranceReportGenerateRequest(BaseModel):
    report_classification: str = Field(default="INTERNAL_ASSURANCE_REPORT", min_length=1)


class CertificationIssueRequest(BaseModel):
    certification_type: str = Field(default="CONTROLLED_OPERATIONAL_STATE", min_length=1)


class CertificationVerifyRequest(BaseModel):
    certification: dict[str, Any] = Field(default_factory=dict)


class VerifyProofRequest(BaseModel):
    execution_id: str = Field(..., min_length=1)
    project_id: str = Field(default="project-employee-rbac")
    payload: dict[str, Any] = Field(default_factory=dict)


class TrustExternalVerifyRequest(BaseModel):
    organization_id: str = Field(..., min_length=1)
    proof_hash: str = Field(..., min_length=16)
    audit_hash: str = Field(..., min_length=16)
    receipt_hash: str = Field(..., min_length=16)
    certification_hash: str | None = None
    signature: str | None = None
    public_key_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class KeyRotateRequest(BaseModel):
    organization_id: str | None = None
    key_family: str = Field(default="audit", min_length=1)
    rotated_by: str = Field(default="system", min_length=1)
    reason: str = Field(default="rotation", min_length=1)


class FederationRegisterRequest(BaseModel):
    peer_organization_id: str = Field(..., min_length=1)
    jurisdiction: str = Field(..., min_length=1)
    role: str = Field(..., min_length=1)
    endpoint: str = Field(..., min_length=1)
    public_key_id: str = Field(..., min_length=1)
    trust_level: str = Field(default="TRUSTED", min_length=1)


class FederationClaimRequest(BaseModel):
    peer_organization_id: str = Field(..., min_length=1)
    claim_type: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class FederationVerifyRequest(BaseModel):
    claim: dict[str, Any] = Field(default_factory=dict)


class EventTopicRequest(BaseModel):
    topic_name: str = Field(..., min_length=1)
    description: str = ""
    retention_days: int = Field(default=0, ge=0)


class EventPublishRequest(BaseModel):
    topic_name: str = Field(..., min_length=1)
    event_type: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)
    partition_key: str = ""
    headers: dict[str, Any] = Field(default_factory=dict)


class EventConsumeRequest(BaseModel):
    topic_name: str | None = None
    after_offset: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1)


class WorkflowStartRequest(BaseModel):
    workflow_name: str = Field(..., min_length=1)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    steps: list[str] | None = None


class WorkflowSignalRequest(BaseModel):
    workflow_id: str = Field(..., min_length=1)
    signal_name: str = Field(..., min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)


class ZeroTrustPolicyRequest(BaseModel):
    policy_name: str = Field(..., min_length=1)
    version: str = Field(default="v1", min_length=1)
    rule_type: str = Field(..., min_length=1)
    rule_payload: dict[str, Any] = Field(default_factory=dict)
    active: bool = True


class ZeroTrustEvaluateRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)
    resource: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class CryptoBackendRegisterRequest(BaseModel):
    backend_name: str = Field(..., min_length=1)
    provider_ref: str = Field(..., min_length=1)
    key_family: str = Field(default="audit", min_length=1)
    key_arn: str | None = None
    hardware_bound: bool = False


class CertificateIssueRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    issuer: str = Field(default="NovaProgramming PKI", min_length=1)
    key_family: str = Field(default="audit", min_length=1)


class TrustFabricRegionRequest(BaseModel):
    region_name: str = Field(..., min_length=1)
    country_code: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    status: str = Field(default="active", min_length=1)


class TrustFabricLinkRequest(BaseModel):
    source_region_id: str = Field(..., min_length=1)
    target_region_id: str = Field(..., min_length=1)
    latency_ms: int = Field(..., ge=0)
    trust_score: int = Field(default=50, ge=0, le=100)
    status: str = Field(default="active", min_length=1)


class TrustFabricSignedRequest(BaseModel):
    peer_organization_id: str = Field(..., min_length=1)
    method: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    headers: dict[str, Any] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)


class TrustFabricSignedRequestVerifyRequest(BaseModel):
    envelope: dict[str, Any] = Field(default_factory=dict)


class IdentityBindRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    device_id: str = Field(..., min_length=1)
    human_trust_score: int = Field(default=50, ge=0, le=100)
    device_trust_score: int = Field(default=50, ge=0, le=100)
    attestation: dict[str, Any] = Field(default_factory=dict)


class RiskPredictionRequest(BaseModel):
    entity_type: str = Field(default="organization", min_length=1)
    entity_id: str | None = None
    horizon_days: int = Field(default=30, ge=1)


class TrustNegotiationRequest(BaseModel):
    peer_organization_id: str = Field(..., min_length=1)
    proposed_terms: dict[str, Any] = Field(default_factory=dict)
    trust_offer: int = Field(default=70, ge=0, le=100)
    trust_floor: int = Field(default=50, ge=0, le=100)


class TrustConsensusRequest(BaseModel):
    proposal: dict[str, Any] = Field(default_factory=dict)
    peer_votes: list[dict[str, Any]] | None = None
    quorum: int | None = Field(default=None, ge=1)


class CertificateTransparencyAppendRequest(BaseModel):
    subject: str = Field(..., min_length=1)
    issuer: str = Field(default="NovaProgramming PKI", min_length=1)
    key_family: str = Field(default="audit", min_length=1)
    status: str = Field(default="active", min_length=1)
    certificate_payload: dict[str, Any] | None = None


class KeyRevocationRequest(BaseModel):
    key_id: str = Field(..., min_length=1)
    reason: str = Field(default="revocation", min_length=1)
    revoked_by: str = Field(default="system", min_length=1)


class TraceSpanRequest(BaseModel):
    actor_user_id: str = Field(..., min_length=1)
    operation_name: str = Field(..., min_length=1)
    endpoint: str = Field(..., min_length=1)
    latency_ms: int = Field(default=0, ge=0)
    status_code: int = Field(default=200, ge=100, le=599)
    policy_decision_id: str | None = None
    proof_hash: str | None = None
    deployment_id: str | None = None
    parent_span_id: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)


class AssuranceSchedulerRunRequest(BaseModel):
    organization_ids: list[str] | None = None


class V9SchemaRequest(BaseModel):
    partition_count: int = Field(default=4, ge=1, le=64)


__all__ = [
    "CloudDeployRequest",
    "CloudRequestDeployRequest",
    "CloudScaleRequest",
    "GovernanceApproveRequest",
    "GovernanceCheckRequest",
    "GovernancePolicyRequest",
    "PolicyCreateRequest",
    "PolicyEvaluateRequest",
    "AssuranceRunRequest",
    "RetentionSetRequest",
    "AssuranceReportGenerateRequest",
    "CertificationIssueRequest",
    "CertificationVerifyRequest",
    "StudioAnalyzeRepoRequest",
    "StudioExplainCodeRequest",
    "StudioGenerateCodeRequest",
    "TrustExternalVerifyRequest",
    "KeyRotateRequest",
    "FederationRegisterRequest",
    "FederationClaimRequest",
    "FederationVerifyRequest",
    "EventTopicRequest",
    "EventPublishRequest",
    "EventConsumeRequest",
    "WorkflowStartRequest",
    "WorkflowSignalRequest",
    "ZeroTrustPolicyRequest",
    "ZeroTrustEvaluateRequest",
    "CryptoBackendRegisterRequest",
    "CertificateIssueRequest",
    "TrustFabricRegionRequest",
    "TrustFabricLinkRequest",
    "TrustFabricSignedRequest",
    "TrustFabricSignedRequestVerifyRequest",
    "IdentityBindRequest",
    "RiskPredictionRequest",
    "TrustNegotiationRequest",
    "TrustConsensusRequest",
    "CertificateTransparencyAppendRequest",
    "KeyRevocationRequest",
    "TraceSpanRequest",
    "AssuranceSchedulerRunRequest",
    "V9SchemaRequest",
    "VerifyProofRequest",
]
