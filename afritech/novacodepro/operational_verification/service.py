from __future__ import annotations

import uuid
from typing import Any

from .enums import CapabilityState, Decision, EvidenceStatus, GADecision, PaymentState, VerificationDomain
from .events import OperationalVerificationEvent
from .evidence import create_evidence_envelope
from .hashing import domain_hash, utc_now
from .models import CapabilityVerification, GovernanceDecision, OperationalVerificationProgram, OperationalVerificationRun, VerificationCheck
from .policy import assert_transition_allowed
from .repository import InMemoryOperationalVerificationRepository


class OperationalVerificationService:
    def __init__(self, repository: InMemoryOperationalVerificationRepository | None = None) -> None:
        self.repository = repository or InMemoryOperationalVerificationRepository()
        self.events: list[OperationalVerificationEvent] = []

    def create_program(self, payload: dict[str, Any]) -> dict[str, Any]:
        program_id = payload.get("id") or f"ovp_{uuid.uuid4().hex}"
        tenant_id = str(payload.get("tenant_id") or "default")
        organization_id = str(payload.get("organization_id") or "novatech")
        release_id = str(payload.get("release_id") or "release-pending")
        capabilities = [
            CapabilityVerification(
                id=f"cap_{domain.value.lower()}",
                tenant_id=tenant_id,
                organization_id=organization_id,
                project_id=str(payload.get("project_id") or "project-pending"),
                product_id=str(payload.get("product_id") or "novacodepro"),
                release_id=release_id,
                environment=str(payload.get("environment") or "ci"),
                region=str(payload.get("region") or "global"),
                version=str(payload.get("version") or "1.0"),
                status=CapabilityState.CONFIGURED,
                created_by=str(payload.get("created_by") or "NovaCodePro"),
                correlation_id=str(payload.get("correlation_id") or program_id),
                domain=domain,
                checks=[VerificationCheck(id=f"check_{domain.value.lower()}_configured", name=f"{domain.value} configured", domain=domain)],
            )
            for domain in (
                VerificationDomain.OBSERVABILITY,
                VerificationDomain.ACCESSIBILITY,
                VerificationDomain.VISUAL_REGRESSION,
                VerificationDomain.DIGITAL_UX_TWIN,
            )
        ]
        program = OperationalVerificationProgram(
            id=program_id,
            tenant_id=tenant_id,
            organization_id=organization_id,
            project_id=str(payload.get("project_id") or "project-pending"),
            product_id=str(payload.get("product_id") or "novacodepro"),
            release_id=release_id,
            environment=str(payload.get("environment") or "ci"),
            region=str(payload.get("region") or "global"),
            version=str(payload.get("version") or "1.0"),
            status=CapabilityState.CONFIGURED,
            created_by=str(payload.get("created_by") or "NovaCodePro"),
            correlation_id=str(payload.get("correlation_id") or program_id),
            capabilities=capabilities,
        )
        self.repository.save_program(program)
        self._publish("OperationalVerificationProgramCreated", "OperationalVerificationProgram", program.id, program.tenant_id, program.organization_id, program.region, program.created_by, "SYSTEM", program.to_dict())
        return program.to_dict()

    def execute_program(self, program_id: str, actor_id: str = "NovaCodePro") -> dict[str, Any]:
        program = self.repository.get_program(program_id)
        if not program:
            raise KeyError("program_not_found")
        assert_transition_allowed(program.status, CapabilityState.RUNNING, actor_type="SYSTEM")
        program.status = CapabilityState.RUNNING
        run = OperationalVerificationRun(
            id=f"ovr_{uuid.uuid4().hex}",
            program_id=program.id,
            tenant_id=program.tenant_id,
            organization_id=program.organization_id,
            project_id=program.project_id,
            product_id=program.product_id,
            release_id=program.release_id,
            environment=program.environment,
            region=program.region,
            version=program.version,
            status=CapabilityState.EXECUTED,
            created_by=actor_id,
            correlation_id=program.correlation_id,
        )
        program.status = CapabilityState.EXECUTED
        self.repository.save_program(program)
        self.repository.save_run(run)
        self._publish("OperationalVerificationCompleted", "OperationalVerificationRun", run.id, run.tenant_id, run.organization_id, run.region, actor_id, "SYSTEM", run.to_dict())
        return run.to_dict()

    def collect_development_evidence(self, evidence_type: str, subject: str, release_id: str, execution_id: str, environment: str = "ci") -> dict[str, Any]:
        evidence = create_evidence_envelope(
            evidence_type=evidence_type,
            producer="NovaCodePro Operational Verification",
            environment=environment,
            subject=subject,
            release_id=release_id,
            execution_id=execution_id,
            artifact_refs=[f"reports/novacodepro/operational-verification/{evidence_type}.json"],
            metrics={"configured": True, "executed": True, "verified": False},
            metadata={"signature_assurance": "DEVELOPMENT_ONLY", "production_evidence": False},
        )
        self.repository.save_evidence(evidence)
        self._publish("EvidenceCollected", "EvidenceEnvelope", evidence.evidence_id, "default", "novatech", "global", "NovaCodePro", "SYSTEM", evidence.to_dict())
        return evidence.to_dict()

    def status(self) -> dict[str, Any]:
        return {
            "repository_status": "operational_verification_automation_v1_implemented",
            "live_environment_status": "operational_verification_automation_v1_evidence_pending",
            "capability_states": [state.value for state in CapabilityState],
            "ga": {"decision": GADecision.GA_BLOCKED.value, "ga_allowed": False, "approval": "PENDING"},
            "payments": {"state": PaymentState.DISABLED.value, "real_payments_enabled": False, "approval": "PENDING"},
            "nova_ai_authority": "ADVISORY_ONLY",
            "events": len(self.events),
            "evidence": len(self.repository.list_evidence()),
        }

    def generate_prr_package(self, release_id: str, environment: str = "ci") -> dict[str, Any]:
        evidence = [item.to_dict() for item in self.repository.list_evidence() if item.release_id == release_id]
        manifest = {
            "prr_id": f"prr_{uuid.uuid4().hex}",
            "release_id": release_id,
            "environment": environment,
            "generated_at": utc_now(),
            "domains": {
                domain: {"status": "PENDING", "evidence_refs": [item["evidence_id"] for item in evidence]}
                for domain in ("quality", "security", "performance", "accessibility", "ux", "operations", "observability")
            },
            "recommendation": "READY_FOR_PRR_APPROVAL" if evidence else "EVIDENCE_PENDING",
            "ga_allowed": False,
            "real_payments_enabled": False,
            "signature_assurance": "DEVELOPMENT_ONLY" if environment != "production" else "SIGNING_PROVIDER_REQUIRED",
        }
        manifest["evidence_manifest_hash"] = domain_hash("novacodepro.prr.manifest", manifest)
        self._publish("PRRPackageGenerated", "PRRPackage", manifest["prr_id"], "default", "novatech", "global", "NovaCodePro", "SYSTEM", manifest)
        return manifest

    def request_executive_approval(self, payload: dict[str, Any], actor_id: str) -> dict[str, Any]:
        return {
            "approval_id": payload.get("approval_id") or f"exec_{uuid.uuid4().hex}",
            "release_id": payload.get("release_id", "release-pending"),
            "prr_id": payload.get("prr_id", "prr-pending"),
            "requested_by": actor_id,
            "requested_at": utc_now(),
            "status": "APPROVAL_PENDING",
            "ga_allowed": False,
            "real_payments_enabled": False,
        }

    def evaluate_ga(self) -> dict[str, Any]:
        return {
            "decision": GADecision.GA_BLOCKED.value,
            "reason": "Server-side GA evaluation requires approved PRR, scoped executive authorization, fresh evidence, deployment verification, rollback, and policy checks.",
            "ga_allowed": False,
            "real_payments_enabled": False,
        }

    def evaluate_payments(self) -> dict[str, Any]:
        return {
            "state": PaymentState.DISABLED.value,
            "finance_approved": False,
            "risk_approved": False,
            "provider_certified": False,
            "settlement_verified": False,
            "reconciliation_verified": False,
            "fraud_verified": False,
            "real_payments_enabled": False,
        }

    def _publish(self, event_type: str, aggregate_type: str, aggregate_id: str, tenant_id: str, organization_id: str, region: str, actor_id: str, actor_type: str, payload: dict[str, Any]) -> None:
        self.events.append(
            OperationalVerificationEvent(
                event_type=event_type,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                tenant_id=tenant_id,
                organization_id=organization_id,
                region=region,
                actor_id=actor_id,
                actor_type=actor_type,
                payload=payload,
                correlation_id=str(payload.get("correlation_id") or aggregate_id),
            )
        )
