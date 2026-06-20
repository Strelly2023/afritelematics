"""FastAPI control-plane router for NovaProgramming staff tools."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.afriprogramming.roles import Role
from afritech.afriprogramming.schemas import (
    AssuranceReportGenerateRequest,
    CertificateIssueRequest,
    CertificateTransparencyAppendRequest,
    AssuranceRunRequest,
    CryptoBackendRegisterRequest,
    IdentityBindRequest,
    EventConsumeRequest,
    EventPublishRequest,
    EventTopicRequest,
    CloudDeployRequest,
    CloudRequestDeployRequest,
    CloudScaleRequest,
    CertificationIssueRequest,
    CertificationVerifyRequest,
    FederationClaimRequest,
    FederationRegisterRequest,
    FederationVerifyRequest,
    KeyRotateRequest,
    GovernanceApproveRequest,
    GovernanceCheckRequest,
    GovernancePolicyRequest,
    PolicyCreateRequest,
    PolicyEvaluateRequest,
    RiskPredictionRequest,
    TrustFabricLinkRequest,
    TrustFabricRegionRequest,
    TrustFabricSignedRequest,
    TrustFabricSignedRequestVerifyRequest,
    TrustConsensusRequest,
    KeyRevocationRequest,
    TraceSpanRequest,
    AssuranceSchedulerRunRequest,
    TrustNegotiationRequest,
    WorkflowSignalRequest,
    WorkflowStartRequest,
    RetentionSetRequest,
    StudioAnalyzeRepoRequest,
    StudioExplainCodeRequest,
    StudioGenerateCodeRequest,
    TrustExternalVerifyRequest,
    ZeroTrustEvaluateRequest,
    ZeroTrustPolicyRequest,
    VerifyProofRequest,
)
from afritech.afriprogramming.control_plane import get_control_plane


def build_afriprogramming_control_router() -> APIRouter:
    control_plane = get_control_plane()
    router = APIRouter(prefix="/v1/novaprogramming", tags=["novaprogramming"])

    @router.get("/status")
    def status() -> dict[str, Any]:
        return control_plane.status()

    @router.get("/catalog")
    def catalog(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.catalog(organization_id=claims.organization_id)

    @router.get("/staff/roles")
    def staff_roles(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        catalog = control_plane.catalog(organization_id=claims.organization_id)
        return {
            "platform": catalog["platform"],
            "roles": catalog["staff_roles"],
            "read_only": True,
        }

    @router.get("/staff/{role}/dashboard")
    def staff_dashboard(
        role: str,
        project_id: str = "project-employee-rbac",
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.staff_dashboard(role, project_id, organization_id=claims.organization_id)

    @router.get("/studio/context/{project_id}")
    def studio_context(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.studio_context(project_id, organization_id=claims.organization_id)

    @router.post("/studio/generate-code")
    def studio_generate_code(
        body: StudioGenerateCodeRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.studio_generate(
            prompt=body.prompt,
            mode=body.mode,
            project_id=body.project_id,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/studio/explain-code")
    def studio_explain_code(
        body: StudioExplainCodeRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.studio_explain(
            code=body.code,
            context=body.context,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/studio/analyze-repo")
    def studio_analyze_repo(
        body: StudioAnalyzeRepoRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.studio_analyze(
            project_id=body.project_id,
            focus=body.focus,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/cloud/services")
    def cloud_services(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.cloud_services(organization_id=claims.organization_id)

    @router.get("/cloud/health")
    def cloud_health(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.cloud_health(organization_id=claims.organization_id)

    @router.post("/cloud/request-deploy")
    def cloud_request_deploy(
        body: CloudRequestDeployRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.cloud_request_deploy(
            service=body.service,
            environment=body.environment,
            image=body.image,
            rationale=body.rationale,
            organization_id=claims.organization_id,
            requested_by=claims.sub,
            requested_role=claims.role,
        )

    @router.post("/cloud/deploy")
    def cloud_deploy(
        body: CloudDeployRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        request = control_plane.audit_log(organization_id=claims.organization_id)
        request_record = next(
            (
                entry
                for entry in request["entries"]
                if entry["event_type"] == "cloud.request_deploy"
                and entry["payload"].get("request_id") == body.request_id
            ),
            None,
        )
        if request_record is None:
            raise HTTPException(status_code=404, detail="deployment request not found")
        service = str(request_record["payload"]["service"]).strip()
        environment = str(request_record["payload"]["environment"]).strip()
        image = str(request_record["payload"]["image"]).strip()
        try:
            return control_plane.cloud_deploy(
                request_id=body.request_id,
                service=service,
                environment=environment,
                image=image,
                organization_id=claims.organization_id,
                deployed_by=claims.sub,
                actor_role=claims.role,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @router.post("/cloud/scale")
    def cloud_scale(
        body: CloudScaleRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.cloud_scale(
            service=body.service,
            replicas=body.replicas,
            organization_id=claims.organization_id,
            deployed_by=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/governance/policy")
    def governance_policy(
        body: GovernancePolicyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.governance_policy(
            policy_name=body.policy_name,
            target=body.target,
            description=body.description,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/governance/audit-log")
    def governance_audit_log(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.audit_log(organization_id=claims.organization_id)

    @router.post("/governance/check")
    def governance_check(
        body: GovernanceCheckRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.governance_check(
            policy_name=body.policy_name,
            target=body.target,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/governance/approve")
    def governance_approve(
        body: GovernanceApproveRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.governance_approve(
            request_id=body.request_id,
            decision=body.decision,
            notes=body.notes,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/intelligence/analyze")
    def intelligence_analyze(
        body: StudioAnalyzeRepoRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.studio_analyze(
            project_id=body.project_id,
            focus=body.focus,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/intelligence/dependencies/{project_id}")
    def intelligence_dependencies(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        analysis = control_plane.studio_analyze(
            project_id=project_id,
            focus="dependencies",
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        return {
            "view": "novaprogramming_dependencies",
            "project": analysis["project"],
            "dependencies": analysis["dependencies"],
            "architecture_signals": analysis["architecture_signals"],
            "read_only": True,
        }

    @router.get("/intelligence/tech-debt/{project_id}")
    def intelligence_tech_debt(
        project_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        analysis = control_plane.studio_analyze(
            project_id=project_id,
            focus="tech_debt",
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        return {
            "view": "novaprogramming_tech_debt",
            "project": analysis["project"],
            "tech_debt_score": analysis["tech_debt_score"],
            "engineering_platform": analysis["engineering_platform"],
            "pr_intelligence": analysis["pr_intelligence"],
            "read_only": True,
        }

    @router.get("/verify/{execution_id}")
    def verify_lookup(
        execution_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        try:
            return control_plane.verify_lookup(execution_id, organization_id=claims.organization_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="proof not found") from exc

    @router.post("/verify/generate-proof")
    def verify_generate_proof(
        body: VerifyProofRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.verify_generate(
            execution_id=body.execution_id,
            project_id=body.project_id,
            payload=body.payload,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/verify/replay/{execution_id}")
    def verify_replay(
        execution_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        try:
            replay = control_plane.verify_replay(
                execution_id,
                organization_id=claims.organization_id,
                actor_user_id=claims.sub,
                actor_role=claims.role,
            )
            return replay
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="proof not found") from exc

    @router.get("/metrics")
    def metrics(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.metrics(organization_id=claims.organization_id)

    @router.get("/trust")
    def trust(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust(organization_id=claims.organization_id)

    @router.get("/trust/stream")
    def trust_stream(
        limit: int = 100,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_stream(organization_id=claims.organization_id, limit=limit)

    @router.get("/trust/anomalies")
    def trust_anomalies(
        limit: int = 25,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_anomalies(organization_id=claims.organization_id, limit=limit)

    @router.post("/trust/verify-external")
    def trust_verify_external(
        body: TrustExternalVerifyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        result = control_plane.trust_verify_external(body.model_dump())
        return {
            "organization_id": claims.organization_id,
            **result,
        }

    @router.get("/trust/risk")
    def trust_risk(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_risk(organization_id=claims.organization_id)

    @router.get("/trust/trends")
    def trust_trends(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_trends(organization_id=claims.organization_id)

    @router.get("/assurance/status")
    def assurance_status(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_status(organization_id=claims.organization_id)

    @router.post("/assurance/run")
    def assurance_run(
        body: AssuranceRunRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_run(
            organization_id=claims.organization_id,
            actor_user_id=body.actor_user_id or claims.sub,
        )

    @router.get("/assurance/history")
    def assurance_history(
        limit: int = 100,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_history(organization_id=claims.organization_id, limit=limit)

    @router.get("/assurance/alerts")
    def assurance_alerts(
        limit: int = 100,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_alerts(organization_id=claims.organization_id, limit=limit)

    @router.get("/trust/replay/{deployment_id}")
    def trust_replay(
        deployment_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        try:
            return control_plane.trust_replay(deployment_id, organization_id=claims.organization_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment not found") from exc

    @router.get("/assurance/{deployment_id}")
    def assurance(
        deployment_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        try:
            return control_plane.assurance(deployment_id, organization_id=claims.organization_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="deployment not found") from exc

    @router.get("/policies")
    def policy_registry(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.policy_registry(organization_id=claims.organization_id)

    @router.post("/policies")
    def policy_create(
        body: PolicyCreateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.policy_create(
            policy_name=body.policy_name,
            version=body.version,
            rule_type=body.rule_type,
            rule_payload=body.rule_payload,
            active=body.active,
            organization_id=claims.organization_id,
            created_by=claims.sub,
        )

    @router.post("/policies/evaluate")
    def policy_evaluate(
        body: PolicyEvaluateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.policy_evaluate(
            action=body.action,
            target=body.target,
            payload=body.payload,
            organization_id=claims.organization_id,
            actor_user_id=claims.sub,
        )

    @router.get("/policies/decisions")
    def policy_decisions(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.policy_decisions(organization_id=claims.organization_id)

    @router.get("/retention")
    def retention(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.retention(organization_id=claims.organization_id)

    @router.post("/retention")
    def retention_set(
        body: RetentionSetRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.retention_set(
            record_type=body.record_type,
            retention_days=body.retention_days,
            legal_hold=body.legal_hold,
            deletion_allowed=body.deletion_allowed,
            organization_id=claims.organization_id,
        )

    @router.get("/retention/check")
    def retention_check(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.retention_check(organization_id=claims.organization_id)

    @router.get("/reports/assurance")
    def assurance_report(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_report(organization_id=claims.organization_id)

    @router.post("/reports/assurance/generate")
    def assurance_report_generate(
        body: AssuranceReportGenerateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_report_generate(
            organization_id=claims.organization_id,
            report_classification=body.report_classification,
        )

    @router.get("/trust/exchange/events")
    def trust_exchange_events(
        limit: int = 100,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_exchange_events(organization_id=claims.organization_id, limit=limit)

    @router.post("/trust/exchange/verify")
    def trust_exchange_verify(
        body: TrustExternalVerifyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        payload = body.model_dump()
        payload.setdefault("payload", {})
        if not payload["payload"]:
            payload["payload"] = {
                "organization_id": body.organization_id,
                "proof_hash": body.proof_hash,
                "audit_hash": body.audit_hash,
                "receipt_hash": body.receipt_hash,
                "certification_hash": body.certification_hash or body.receipt_hash,
                "public_key_id": body.public_key_id or "nova-cert-key-1",
            }
        result = control_plane.trust_exchange_verify(receipt=payload, organization_id=claims.organization_id)
        return {
            "organization_id": claims.organization_id,
            **result,
        }

    @router.get("/certification")
    def certification(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.certification(organization_id=claims.organization_id)

    @router.post("/certification/issue")
    def certification_issue(
        body: CertificationIssueRequest,
        claims = Depends(require_roles(Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.certification_issue(
            organization_id=claims.organization_id,
            certification_type=body.certification_type,
            actor_user_id=claims.sub,
        )

    @router.post("/certification/verify")
    def certification_verify(
        body: CertificationVerifyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.certification_verify(body.certification)

    @router.get("/keys")
    def key_registry(
        key_family: str = "audit",
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.key_registry(organization_id=claims.organization_id, key_family=key_family)

    @router.post("/keys/rotate")
    def key_rotate(
        body: KeyRotateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.key_rotate(
            organization_id=body.organization_id or claims.organization_id,
            key_family=body.key_family,
            rotated_by=body.rotated_by or claims.sub,
            reason=body.reason,
        )

    @router.get("/audit/signed")
    def signed_audit_chain(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.signed_audit_chain(organization_id=claims.organization_id)

    @router.get("/audit/signed/verify")
    def signed_audit_verify(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.signed_audit_verify(organization_id=claims.organization_id)

    @router.get("/network/distributed")
    def distributed_trust_network(
        quorum: int = 2,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.distributed_trust_network(organization_id=claims.organization_id, quorum=quorum)

    @router.post("/federation/register")
    def federation_register(
        body: FederationRegisterRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.federation_register(
            peer_organization_id=body.peer_organization_id,
            jurisdiction=body.jurisdiction,
            role=body.role,
            endpoint=body.endpoint,
            public_key_id=body.public_key_id,
            trust_level=body.trust_level,
            organization_id=claims.organization_id,
        )

    @router.post("/federation/claim")
    def federation_claim(
        body: FederationClaimRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.federation_claim(
            peer_organization_id=body.peer_organization_id,
            claim_type=body.claim_type,
            payload=body.payload,
            organization_id=claims.organization_id,
        )

    @router.post("/federation/verify")
    def federation_verify(
        body: FederationVerifyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.federation_verify(
            claim=body.claim,
            organization_id=claims.organization_id,
        )

    @router.get("/stream/topics")
    def stream_topics(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.event_topics(organization_id=claims.organization_id)

    @router.post("/stream/topics")
    @router.post("/stream/topics/create")
    def stream_topics_create(
        body: EventTopicRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.event_topic_create(
            topic_name=body.topic_name,
            description=body.description,
            retention_days=body.retention_days,
            organization_id=claims.organization_id,
        )

    @router.post("/stream/publish")
    def stream_publish(
        body: EventPublishRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.event_publish(
            topic_name=body.topic_name,
            event_type=body.event_type,
            payload=body.payload,
            partition_key=body.partition_key,
            headers=body.headers,
            organization_id=claims.organization_id,
        )

    @router.get("/stream/consume")
    def stream_consume(
        topic_name: str | None = None,
        after_offset: int = 0,
        limit: int = 100,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.event_consume(
            topic_name=topic_name,
            after_offset=after_offset,
            limit=limit,
            organization_id=claims.organization_id,
        )

    @router.post("/workflows/start")
    def workflow_start(
        body: WorkflowStartRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.workflow_start(
            workflow_name=body.workflow_name,
            input_payload=body.input_payload,
            steps=body.steps,
            organization_id=claims.organization_id,
        )

    @router.post("/workflows/signal")
    def workflow_signal(
        body: WorkflowSignalRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.workflow_signal(
            workflow_id=body.workflow_id,
            signal_name=body.signal_name,
            payload=body.payload,
            organization_id=claims.organization_id,
        )

    @router.get("/workflows/{workflow_id}")
    def workflow_status(
        workflow_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.workflow_status(
            workflow_id=workflow_id,
            organization_id=claims.organization_id,
        )

    @router.get("/workflows/{workflow_id}/history")
    def workflow_history(
        workflow_id: str,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.workflow_history(
            workflow_id=workflow_id,
            organization_id=claims.organization_id,
        )

    @router.get("/zero-trust/policies")
    def zero_trust_policies(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.zero_trust_policies(organization_id=claims.organization_id)

    @router.post("/zero-trust/policies")
    def zero_trust_policy_create(
        body: ZeroTrustPolicyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.zero_trust_create(
            policy_name=body.policy_name,
            version=body.version,
            rule_type=body.rule_type,
            rule_payload=body.rule_payload,
            active=body.active,
            organization_id=claims.organization_id,
            created_by=claims.sub,
        )

    @router.post("/zero-trust/evaluate")
    def zero_trust_evaluate(
        body: ZeroTrustEvaluateRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.zero_trust_evaluate(
            subject=body.subject,
            action=body.action,
            resource=body.resource,
            context=body.context,
            organization_id=claims.organization_id,
        )

    @router.get("/zero-trust/decisions")
    def zero_trust_decisions(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.zero_trust_decisions(organization_id=claims.organization_id)

    @router.get("/crypto/backends")
    def crypto_backends(
        key_family: str | None = None,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.crypto_backends(organization_id=claims.organization_id, key_family=key_family)

    @router.post("/crypto/backends")
    def crypto_backend_register(
        body: CryptoBackendRegisterRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.crypto_backend_register(
            backend_name=body.backend_name,
            provider_ref=body.provider_ref,
            key_family=body.key_family,
            key_arn=body.key_arn,
            hardware_bound=body.hardware_bound,
            organization_id=claims.organization_id,
        )

    @router.get("/crypto/chains")
    def certificate_chains(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.certificate_chains(organization_id=claims.organization_id)

    @router.post("/crypto/chains")
    def certificate_issue(
        body: CertificateIssueRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.certificate_issue(
            subject=body.subject,
            issuer=body.issuer,
            key_family=body.key_family,
            organization_id=claims.organization_id,
        )

    @router.post("/crypto/chains/verify")
    def certificate_verify(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.certificate_verify(organization_id=claims.organization_id)

    @router.get("/stream/backends")
    def stream_backends(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.stream_backends(organization_id=claims.organization_id)

    @router.post("/stream/backends")
    def stream_backend_register(
        body: EventTopicRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.stream_backend_register(
            backend_name=body.topic_name,
            provider=body.description or "redis-streams",
            region="global",
            partitions=max(1, body.retention_days or 1),
            organization_id=claims.organization_id,
        )

    @router.get("/trust/fabric/regions")
    def trust_fabric_regions(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_fabric_regions(organization_id=claims.organization_id)

    @router.post("/trust/fabric/regions")
    def trust_fabric_region_register(
        body: TrustFabricRegionRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.trust_fabric_region_register(
            region_name=body.region_name,
            country_code=body.country_code,
            provider=body.provider,
            status=body.status,
            organization_id=claims.organization_id,
        )

    @router.post("/trust/fabric/regions/link")
    def trust_fabric_link(
        body: TrustFabricLinkRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.trust_fabric_link(
            source_region_id=body.source_region_id,
            target_region_id=body.target_region_id,
            latency_ms=body.latency_ms,
            trust_score=body.trust_score,
            status=body.status,
            organization_id=claims.organization_id,
        )

    @router.get("/trust/fabric/graph")
    def decentralized_trust_graph(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.decentralized_trust_graph(organization_id=claims.organization_id)

    @router.post("/trust/fabric/http-request")
    def trust_fabric_signed_request(
        body: TrustFabricSignedRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.trust_fabric_signed_request(
            peer_organization_id=body.peer_organization_id,
            method=body.method,
            url=body.url,
            headers=body.headers,
            body=body.body,
            organization_id=claims.organization_id,
        )

    @router.post("/trust/fabric/http-request/verify")
    def trust_fabric_signed_request_verify(
        body: TrustFabricSignedRequestVerifyRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_fabric_signed_request_verify(
            envelope=body.envelope,
            organization_id=claims.organization_id,
        )

    @router.post("/identity/bind")
    def identity_bind(
        body: IdentityBindRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.identity_bind(
            user_id=body.user_id,
            device_id=body.device_id,
            human_trust_score=body.human_trust_score,
            device_trust_score=body.device_trust_score,
            attestation=body.attestation,
            organization_id=claims.organization_id,
        )

    @router.get("/identity/bindings")
    def identity_bindings(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.identity_bindings(organization_id=claims.organization_id)

    @router.post("/risk/predict")
    def risk_prediction(
        body: RiskPredictionRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.risk_prediction(
            entity_type=body.entity_type,
            entity_id=body.entity_id,
            horizon_days=body.horizon_days,
            organization_id=claims.organization_id,
        )

    @router.get("/risk/predictions")
    def risk_predictions(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.risk_predictions(organization_id=claims.organization_id)

    @router.post("/negotiation/start")
    def trust_negotiation(
        body: TrustNegotiationRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.trust_negotiation(
            peer_organization_id=body.peer_organization_id,
            proposed_terms=body.proposed_terms,
            trust_offer=body.trust_offer,
            trust_floor=body.trust_floor,
            organization_id=claims.organization_id,
        )

    @router.get("/negotiation/sessions")
    def trust_negotiations(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trust_negotiations(organization_id=claims.organization_id)

    @router.get("/billing/summary")
    def billing_summary(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.billing_summary(organization_id=claims.organization_id)

    @router.get("/insights")
    def insights(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.insights(organization_id=claims.organization_id)

    @router.get("/v9/schema")
    def v9_schema(
        partition_count: int = 4,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.v9_schema(partition_count=partition_count)

    @router.post("/v9/trust/consensus")
    def v9_trust_consensus(
        body: TrustConsensusRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.trust_consensus(
            organization_id=claims.organization_id,
            proposal=body.proposal,
            peer_votes=body.peer_votes,
            quorum=body.quorum,
        )

    @router.post("/v9/certificate-transparency")
    def v9_certificate_transparency_append(
        body: CertificateTransparencyAppendRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.certificate_transparency_append(
            organization_id=claims.organization_id,
            subject=body.subject,
            issuer=body.issuer,
            key_family=body.key_family,
            status=body.status,
            certificate_payload=body.certificate_payload,
        )

    @router.get("/v9/certificate-transparency")
    def v9_certificate_transparency_log(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.certificate_transparency_log(organization_id=claims.organization_id)

    @router.post("/v9/keys/revoke")
    def v9_key_revocation(
        body: KeyRevocationRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER)),
    ) -> dict[str, Any]:
        return control_plane.key_revocation(
            organization_id=claims.organization_id,
            key_id=body.key_id,
            reason=body.reason,
            revoked_by=body.revoked_by or claims.sub,
        )

    @router.get("/v9/keys/revocations")
    def v9_key_revocations(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.key_revocations(organization_id=claims.organization_id)

    @router.post("/v9/traces")
    def v9_trace_span(
        body: TraceSpanRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        return control_plane.trace_span(
            organization_id=claims.organization_id,
            actor_user_id=body.actor_user_id,
            operation_name=body.operation_name,
            endpoint=body.endpoint,
            latency_ms=body.latency_ms,
            status_code=body.status_code,
            policy_decision_id=body.policy_decision_id,
            proof_hash=body.proof_hash,
            deployment_id=body.deployment_id,
            parent_span_id=body.parent_span_id,
            attributes=body.attributes,
        )

    @router.get("/v9/traces")
    def v9_trace_spans(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.trace_spans(organization_id=claims.organization_id)

    @router.post("/v9/assurance/scheduler/run")
    def v9_assurance_scheduler_run(
        body: AssuranceSchedulerRunRequest,
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.DEVELOPER)),
    ) -> dict[str, Any]:
        organization_ids = body.organization_ids or [claims.organization_id]
        return control_plane.assurance_scheduler_run(organization_ids=organization_ids)

    @router.get("/v9/assurance/scheduler/history")
    def v9_assurance_scheduler_history(
        claims = Depends(require_roles(Role.OPERATOR, Role.VERIFIER, Role.OBSERVER)),
    ) -> dict[str, Any]:
        return control_plane.assurance_scheduler_history(organization_id=claims.organization_id)

    return router


__all__ = ["build_afriprogramming_control_router"]
