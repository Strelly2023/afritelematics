from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256
from typing import Any

from afritech.afroprog_workspace.models import afroprog_seed_projects, ProjectWorkspace
from afritech.afriprogramming.persistence import DEFAULT_ORGANIZATION_ID
from afritech.novascript.v2.adoption import (
    get_external_audit_marketplace,
    get_field_adoption_registry,
    get_novascript_standard_profile,
    get_platform_integration_registry,
    get_production_evidence_registry,
)
from afritech.novascript.v2.certificates import get_novatrust_certificate_authority
from afritech.novascript.v2.compliance import get_ai_regulatory_compliance_layer
from afritech.novascript.v2.economy import (
    get_autonomous_self_upgrade_engine,
    get_global_trust_network,
    get_tokenized_trust_economy,
)
from afritech.novascript.v2.explainability import (
    get_architecture_observatory,
    get_assurance_drift_engine,
    get_decision_explainability_engine,
    get_portable_verification_packager,
)
from afritech.novascript.v2.graph import get_repository_graph_intelligence
from afritech.novascript.v2.federation import get_novascript_federation
from afritech.novascript.v2.intelligence import (
    get_architecture_evolution_ledger,
    get_continuous_assurance_engine,
    get_continuous_repository_intelligence,
    get_deployment_feedback_loop,
)
from afritech.novascript.v2.knowledge import get_architecture_knowledge_base
from afritech.novascript.v2.memory import get_workspace_memory_store
from afritech.novascript.v2.monitoring import (
    get_continuous_assurance_monitor,
    get_evidence_retention_governance,
    get_formal_assurance_reporter,
    get_opentelemetry_bridge,
)
from afritech.novascript.v2.parser import get_structured_output_parser
from afritech.novascript.v2.persistence import get_canonical_persistence_store
from afritech.novascript.v2.policy import get_policy_registry, get_policy_trust_engine
from afritech.novascript.v2.prompts import get_prompt_registry
from afritech.novascript.v2.providers import ModelProviderLayer, PromptExecutionRequest
from afritech.novascript.v2.receipts import get_governance_receipt_store
from afritech.novascript.v2.remediation import (
    get_autonomous_remediation_engine,
    get_deployment_agent_orchestrator,
)
from afritech.novascript.v2.tools import get_tool_registry
from afritech.novascript.v2.workflow import get_agent_workflow_engine
from afritech.sdk.novascript import validate_artifact as validate_novascript_artifact


class NovaScriptV2Engine:
    def __init__(self) -> None:
        self.prompts = get_prompt_registry()
        self.provider_layer = ModelProviderLayer()
        self.tools = get_tool_registry()
        self.memory = get_workspace_memory_store()
        self.graph = get_repository_graph_intelligence()
        self.knowledge = get_architecture_knowledge_base()
        self.parser = get_structured_output_parser()
        self.receipts = get_governance_receipt_store()
        self.workflow = get_agent_workflow_engine()
        self.policy_trust = get_policy_trust_engine()
        self.policy_registry = get_policy_registry()
        self.federation = get_novascript_federation()
        self.deployment_feedback = get_deployment_feedback_loop()
        self.continuous_intelligence = get_continuous_repository_intelligence()
        self.assurance = get_continuous_assurance_engine()
        self.architecture_ledger = get_architecture_evolution_ledger()
        self.certificates = get_novatrust_certificate_authority()
        self.remediation = get_autonomous_remediation_engine()
        self.deployment_agents = get_deployment_agent_orchestrator()
        self.persistence = get_canonical_persistence_store()
        self.telemetry = get_opentelemetry_bridge()
        self.assurance_monitor = get_continuous_assurance_monitor()
        self.retention = get_evidence_retention_governance()
        self.assurance_reporter = get_formal_assurance_reporter()
        self.global_trust_network = get_global_trust_network()
        self.trust_economy = get_tokenized_trust_economy()
        self.self_upgrade = get_autonomous_self_upgrade_engine()
        self.regulatory_compliance = get_ai_regulatory_compliance_layer()
        self.standard_profile = get_novascript_standard_profile()
        self.integrations = get_platform_integration_registry()
        self.field_adoption = get_field_adoption_registry()
        self.production_evidence = get_production_evidence_registry()
        self.audit_marketplace = get_external_audit_marketplace()
        self.explainability = get_decision_explainability_engine()
        self.drift_engine = get_assurance_drift_engine()
        self.verification_packager = get_portable_verification_packager()
        self.architecture_observatory = get_architecture_observatory()

    def status(self, organization_id: str | None = None) -> dict[str, Any]:
        return {
            "version": "NovaScript V7",
            "model_layer": self.provider_layer.status(),
            "workspace_memory": True,
            "persistent_evolving_memory": True,
            "tool_calling": True,
            "tool_error_handling": "structured",
            "repository_graph_intelligence": True,
            "agent_workflow": True,
            "planning_engine": True,
            "deterministic_artifacts": True,
            "trust_evolution_analytics": True,
            "policy_driven_trust_engine": True,
            "cross_system_federation": True,
            "cross_organization_federation": True,
            "policy_dsl": True,
            "policy_registry": True,
            "deployment_feedback_loop": True,
            "deployment_ai_agents": True,
            "trust_forecasting": True,
            "continuous_assurance": True,
            "architecture_evolution_tracking": True,
            "architecture_evolution_ledger": True,
            "continuous_repository_intelligence": True,
            "engineering_risk_scoring": True,
            "technical_debt_prediction": True,
            "enterprise_knowledge_graph": True,
            "autonomous_engineering_workflows": True,
            "autonomous_remediation": True,
            "external_audit_api": True,
            "certificate_chain_verification": True,
            "postgresql_canonical_persistence": True,
            "signed_certification_authority_hierarchy": True,
            "continuous_assurance_monitoring_service": True,
            "policy_registry_lifecycle_management": True,
            "trust_trend_analytics": True,
            "opentelemetry_integration": True,
            "organization_risk_dashboards": True,
            "evidence_retention_governance": True,
            "multi_organization_trust_network": True,
            "formal_assurance_reporting": True,
            "global_trust_network": True,
            "tokenized_trust_economy": True,
            "autonomous_self_upgrading_systems": True,
            "ai_regulatory_compliance_layer": True,
            "novascript_trust_standard": True,
            "platform_plugin_registry": True,
            "field_adoption": True,
            "real_organization_onboarding": True,
            "real_audit_packages": True,
            "real_production_evidence": True,
            "audit_marketplace": True,
            "canonical_doctrine_layer": True,
            "decision_explainability": True,
            "federated_trust_graph": True,
            "assurance_drift_detection": True,
            "portable_verification_package": True,
            "formal_standard_family": True,
            "adoption_certification_program": True,
            "public_trust_portal": True,
            "architecture_evolution_observatory": True,
            "prompt_registry": True,
            "governance_receipts": True,
            "structured_output_parser": True,
            "organization_id": organization_id or DEFAULT_ORGANIZATION_ID,
        }

    def execute(
        self,
        *,
        prompt: str,
        project_id: str | None = None,
        organization_id: str | None = None,
        language: str = "python",
        mode: str = "code",
        intent: str = "generate",
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        org_id = organization_id or DEFAULT_ORGANIZATION_ID
        project = _select_project(project_id)
        request = PromptExecutionRequest(
            intent=intent,
            prompt=prompt,
            project=project,
            organization_id=org_id,
            language=language,
            mode=mode,
            context=context or {},
        )
        memory_before = self.memory.snapshot(organization_id=org_id, project_id=project.project_id)
        workflow = self.workflow.start(
            organization_id=org_id,
            project_id=project.project_id,
            intent=intent,
            memory_count=int(memory_before.get("memory_count", 0)),
        )
        provider_result = self.provider_layer.execute(request)
        graph_summary = self.graph.summarize(project)
        architecture = self.tools.execute(
            "architecture_kb",
            prompt=prompt,
            project=project,
            intent=intent,
        ).output
        multi_file = self.tools.execute(
            "multi_file_generation",
            prompt=prompt,
            project=project,
            intent=intent,
            language=language,
            mode=mode,
            architecture=architecture,
        ).output
        debt = self.tools.execute(
            "debt_analysis",
            project=project,
            graph=graph_summary,
        ).output
        trust = self.tools.execute(
            "trust_review",
            prompt=prompt,
            graph=graph_summary,
            debt=debt,
            architecture=architecture,
        ).output
        policy_trust = self.policy_trust.evaluate(
            prompt=prompt,
            graph=graph_summary,
            debt=debt,
            architecture=architecture,
            deterministic_artifacts=True,
        )
        trust = {
            **trust,
            "trust_score": policy_trust["trust_score"],
            "status": policy_trust["status"],
            "policy_review": policy_trust,
        }
        parsed = self.parser.parse(provider_result.raw_output).data
        tool_calls = parsed.get("tool_calls", [])
        tool_results = self.tools.execute_many(tool_calls if isinstance(tool_calls, list) else [])
        deployment_snapshot = self.deployment_feedback.snapshot(organization_id=org_id, project_id=project.project_id)
        continuous_intelligence = self.continuous_intelligence.analyze(
            project_id=project.project_id,
            graph=graph_summary,
            debt=debt,
            memory=memory_before,
            trust=policy_trust,
            deployment_feedback=deployment_snapshot,
        )
        federation_consensus = self.federation.consensus(
            project_id=project.project_id,
            payload={
                "intent": parsed.get("intent", intent),
                "trust_score": policy_trust["trust_score"],
                "risk_score": continuous_intelligence["engineering_risk"]["risk_score"],
            },
        )
        policy_decision = self.policy_trust.evaluate_dsl(
            context={
                "trust_score": policy_trust["trust_score"],
                "risk_score": continuous_intelligence["engineering_risk"]["risk_score"],
                "federation_verified": federation_consensus["verified"],
                "receipt_verified": True,
            }
        )
        continuous_assurance = self.assurance.assess(
            project_id=project.project_id,
            trust=policy_trust,
            risk=continuous_intelligence["engineering_risk"],
            policy_decision=policy_decision,
            architecture=continuous_intelligence["architecture_evolution"],
        )
        architecture_ledger = self.architecture_ledger.record(
            project_id=project.project_id,
            architecture=continuous_intelligence["architecture_evolution"],
            decision=policy_decision,
            knowledge_graph=continuous_intelligence["enterprise_knowledge_graph"],
        )
        autonomous_remediation = self.remediation.plan(
            project_id=project.project_id,
            risk=continuous_intelligence["engineering_risk"],
            debt_prediction=continuous_intelligence["technical_debt_prediction"],
            policy_trust=policy_trust,
        )
        deployment_agents = self.deployment_agents.plan(
            project_id=project.project_id,
            environment=str((context or {}).get("environment", "staging")),
            risk=continuous_intelligence["engineering_risk"],
            trust_forecast=continuous_intelligence["trust_forecast"],
        )
        output_payload = {
            "provider": provider_result.provider_name,
            "model_name": provider_result.model_name,
            "intent": parsed.get("intent", intent),
            "project_id": project.project_id,
            "organization_id": org_id,
            "prompt": prompt,
            "language": language,
            "mode": mode,
            "parsed_output": parsed,
            "tool_results": tool_results,
            "model_routing": {
                "selected_provider": provider_result.provider_name,
                "selected_model": provider_result.model_name,
                "intent": parsed.get("intent", intent),
            },
            "multi_provider_orchestration": provider_result.orchestration,
            "repository_graph": graph_summary,
            "architecture_knowledge": architecture,
            "generated_files": multi_file.get("generated_files", []),
            "technical_debt": debt,
            "technical_debt_prediction": continuous_intelligence["technical_debt_prediction"],
            "trust_review": trust,
            "policy_trust": policy_trust,
            "policy_decision": policy_decision,
            "policy_registry": {
                "mode": "policy_dsl_registry",
                "policies": self.policy_registry.list(),
            },
            "trust_forecast": continuous_intelligence["trust_forecast"],
            "engineering_risk": continuous_intelligence["engineering_risk"],
            "architecture_evolution": continuous_intelligence["architecture_evolution"],
            "architecture_evolution_ledger": architecture_ledger,
            "enterprise_knowledge_graph": continuous_intelligence["enterprise_knowledge_graph"],
            "autonomous_engineering_workflows": continuous_intelligence["autonomous_workflows"],
            "autonomous_remediation": autonomous_remediation,
            "deployment_ai_agents": deployment_agents,
            "continuous_assurance": continuous_assurance,
            "continuous_repository_intelligence": continuous_intelligence,
            "deployment_feedback": deployment_snapshot,
            "federation": federation_consensus,
            "planning_engine": {
                "mode": "true_agent_behavior",
                "plan": [asdict(step) for step in workflow.steps],
                "memory_consulted": memory_before.get("memory_count", 0),
                "autonomous_workflows": continuous_intelligence["autonomous_workflows"],
            },
            "workflow": {
                "workflow_id": workflow.workflow_id,
                "status": workflow.status,
                "steps": [asdict(step) for step in workflow.steps],
            },
        }
        receipt = self.receipts.issue(
            organization_id=org_id,
            project_id=project.project_id,
            prompt=prompt,
            output=output_payload,
            trust_score=int(trust.get("trust_score", 0)),
            status=str(trust.get("status", "needs_review")),
        )
        certificate_chain = self.certificates.issue_chain(
            organization_id=org_id,
            project_id=project.project_id,
            receipt=receipt.canonical_dict(),
            federation=federation_consensus,
        )
        trust_exchange = self.federation.trust_exchange(
            issuer_org=org_id,
            subject_org="external-auditor",
            receipt_hash=receipt.output_hash,
            trust_score=int(trust.get("trust_score", 0)),
        )
        self.global_trust_network.join(organization_id=org_id, trust_domain="tenant", trust_score=int(trust.get("trust_score", 0)))
        self.global_trust_network.join(organization_id="external-auditor", trust_domain="audit", trust_score=85)
        trust_token = self.trust_economy.mint(
            organization_id=org_id,
            receipt_hash=receipt.output_hash,
            trust_score=int(trust.get("trust_score", 0)),
        )
        assurance_monitoring = self.assurance_monitor.observe(
            organization_id=org_id,
            project_id=project.project_id,
            assurance=continuous_assurance,
            risk=continuous_intelligence["engineering_risk"],
            trust=policy_trust,
        )
        retention_policy = self.retention.policy(organization_id=org_id, project_id=project.project_id)
        formal_assurance_report = self.assurance_reporter.report(
            organization_id=org_id,
            project_id=project.project_id,
            assurance=continuous_assurance,
            certificate_chain=certificate_chain,
            policy_decision=policy_decision,
        )
        production_evidence_snapshot = self.production_evidence.snapshot(
            organization_id=org_id,
            project_id=project.project_id,
        )
        audit_package = self.audit_marketplace.package(
            organization_id=org_id,
            project_id=project.project_id,
            receipt=receipt.canonical_dict(),
            certificate_chain=certificate_chain,
            assurance_report=formal_assurance_report,
            production_evidence=production_evidence_snapshot,
        )
        regulatory_compliance = self.regulatory_compliance.assess(
            organization_id=org_id,
            project_id=project.project_id,
            policy_decision=policy_decision,
            certificate_chain=certificate_chain,
            assurance=continuous_assurance,
        )
        decision_explanation = self.explainability.explain(
            decision="deploy_allowed" if policy_decision.get("allowed") else "deploy_review",
            policy_decision=policy_decision,
            trust=policy_trust,
            certificate_chain=certificate_chain,
            assurance=continuous_assurance,
        )
        assurance_drift = self.drift_engine.detect(
            assurance=continuous_assurance,
            compliance=regulatory_compliance,
            architecture=continuous_intelligence["architecture_evolution"],
            evidence=production_evidence_snapshot,
        )
        architecture_observatory = self.architecture_observatory.observe(
            project_id=project.project_id,
            ledger=architecture_ledger,
            trust=policy_trust,
            risk=continuous_intelligence["engineering_risk"],
        )
        adoption_certification = self.field_adoption.certify(
            organization_id=org_id,
            trust_score=int(trust.get("trust_score", 0)),
            evidence_count=int(production_evidence_snapshot.get("verified_count", 0)),
            audit_verified=True,
        )
        self_upgrade_plan = self.self_upgrade.plan(
            project_id=project.project_id,
            assurance=continuous_assurance,
            risk=continuous_intelligence["engineering_risk"],
        )
        telemetry_span = self.telemetry.emit_span(
            name="novascript.execute",
            attributes={
                "organization_id": org_id,
                "project_id": project.project_id,
                "intent": str(parsed.get("intent", intent)),
                "trust_score": int(trust.get("trust_score", 0)),
                "risk_score": int(continuous_intelligence["engineering_risk"]["risk_score"]),
            },
        )
        canonical_record = self.persistence.persist(
            organization_id=org_id,
            project_id=project.project_id,
            record_type="novascript_execution",
            payload={
                "receipt_id": receipt.receipt_id,
                "policy_decision_id": policy_decision["decision_id"],
                "certificate_chain_id": certificate_chain["chain_id"],
                "assurance_report_id": formal_assurance_report["report_id"],
            },
        )
        portable_verification_package = self.verification_packager.package(
            receipt=receipt.canonical_dict(),
            certificate_chain=certificate_chain,
            assurance_report=formal_assurance_report,
            proof={
                "policy_decision_id": policy_decision.get("decision_id"),
                "federation_id": federation_consensus.get("federation_id"),
                "trust_exchange_id": trust_exchange.get("exchange_id"),
                "canonical_record_id": canonical_record.get("record_id"),
            },
            explanation=decision_explanation,
        )
        trust_analytics = self.receipts.trust_analytics(organization_id=org_id, project_id=project.project_id)
        memory_record = self.memory.append(
            organization_id=org_id,
            project_id=project.project_id,
            intent=intent,
            prompt=prompt,
            summary={
                "provider": provider_result.provider_name,
                "intent": parsed.get("intent", intent),
                "trust_status": trust.get("status", "needs_review"),
                "trust_score": trust.get("trust_score", 0),
                "risk_score": continuous_intelligence["engineering_risk"]["risk_score"],
                "architecture_version": continuous_intelligence["architecture_evolution"]["architecture_version"],
            },
            receipts=[receipt.canonical_dict()],
        )
        output_payload.update(
            {
                "memory": memory_record.__dict__,
                "memory_evolution": self.memory.snapshot(organization_id=org_id, project_id=project.project_id).get(
                    "evolution", {}
                ),
                "governance_receipt": receipt.canonical_dict(),
                "certificate_chain": certificate_chain,
                "trust_exchange": trust_exchange,
                "trust_token": trust_token,
                "global_trust_network": self.global_trust_network.status(),
                "canonical_persistence": canonical_record,
                "persistence_status": self.persistence.status(),
                "assurance_monitoring": assurance_monitoring,
                "organization_risk_dashboard": self.assurance_monitor.risk_dashboard(organization_id=org_id),
                "evidence_retention": retention_policy,
                "formal_assurance_report": formal_assurance_report,
                "audit_marketplace_package": audit_package,
                "standard_profile": self.standard_profile.profile(),
                "decision_explainability": decision_explanation,
                "trust_graph": self.federation.trust_graph(),
                "assurance_drift": assurance_drift,
                "portable_verification_package": portable_verification_package,
                "adoption_certification": adoption_certification,
                "architecture_observatory": architecture_observatory,
                "platform_integrations": {
                    "mode": "platform_others_plug_into",
                    "integrations": self.integrations.list(organization_id=org_id),
                },
                "field_adoption": self.field_adoption.status(),
                "production_evidence": production_evidence_snapshot,
                "regulatory_compliance": regulatory_compliance,
                "self_upgrade_plan": self_upgrade_plan,
                "opentelemetry": telemetry_span,
                "trust_evolution": trust_analytics,
                "receipt_id": receipt.receipt_id,
                "response_hash": sha256(
                    f"{prompt}:{project.project_id}:{language}:{mode}:{provider_result.model_name}".encode("utf-8")
                ).hexdigest(),
                "execution_preview": {
                    "sandboxed": True,
                    "mutation_allowed": False,
                    "next_step": "governance review in NovaProgramming",
                },
            }
        )
        return _strip_timestamp_fields(output_payload)

    def explain(
        self,
        *,
        code: str,
        context: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Explain the provided code.\nContext: {context}\nCode:\n{code}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="explain",
            context={"code": code, "context": context},
        )

    def debug(
        self,
        *,
        code: str = "",
        error: str = "",
        context: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Debug the failure.\nError: {error}\nContext: {context}\nCode:\n{code}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="debug",
            context={"code": code, "error": error, "context": context},
        )

    def architecture(
        self,
        *,
        description: str,
        stack: str,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Design architecture.\nDescription: {description}\nStack: {stack}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="architecture",
            context={"description": description, "stack": stack},
        )

    def tests(
        self,
        *,
        target: str,
        framework: str = "pytest",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Generate tests for {target} using {framework}"
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="tests",
            context={"target": target, "framework": framework},
        )

    def docs(
        self,
        *,
        topic: str,
        audience: str = "developer",
        format: str = "README",
        metadata: dict[str, Any] | None = None,
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        prompt = f"Write documentation for {topic}."
        return self.execute(
            prompt=prompt,
            project_id="project-employee-rbac",
            organization_id=organization_id,
            intent="docs",
            context={"topic": topic, "audience": audience, "format": format, "metadata": metadata or {}},
        )

    def repository_intelligence(
        self,
        *,
        project_id: str | None = None,
        focus: str = "",
        organization_id: str | None = None,
    ) -> dict[str, Any]:
        project = _select_project(project_id)
        return self.execute(
            prompt=f"Analyze repository intelligence for {project.name}. Focus: {focus}",
            project_id=project.project_id,
            organization_id=organization_id,
            intent="repo_intelligence",
            context={"focus": focus},
        )

    def memory_snapshot(self, *, organization_id: str, project_id: str) -> dict[str, Any]:
        return self.memory.snapshot(organization_id=organization_id, project_id=project_id)

    def prompt_catalog(self) -> list[dict[str, Any]]:
        return self.prompts.list()

    def receipt_history(self, *, organization_id: str, project_id: str | None = None) -> list[dict[str, Any]]:
        return self.receipts.recent(organization_id=organization_id, project_id=project_id)

    def trust_analytics(self, *, organization_id: str, project_id: str | None = None) -> dict[str, Any]:
        return self.receipts.trust_analytics(organization_id=organization_id, project_id=project_id)

    def verify_receipt(self, receipt: dict[str, Any]) -> dict[str, Any]:
        return self.receipts.verify(receipt)

    def verify_audit_package(self, package: dict[str, Any]) -> dict[str, Any]:
        receipt = package.get("receipt", {})
        chain = package.get("certificate_chain", {})
        receipt_verification = self.receipts.verify(receipt if isinstance(receipt, dict) else {})
        chain_verification = self.certificates.verify_chain(
            receipt=receipt if isinstance(receipt, dict) else {},
            chain=chain if isinstance(chain, dict) else {},
            receipt_verification=receipt_verification,
        )
        return {
            "mode": "external_audit_verification",
            "verified": bool(receipt_verification.get("verified")) and bool(chain_verification.get("verified")),
            "receipt": receipt_verification,
            "certificate_chain": chain_verification,
        }

    def validate_artifact(self, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_novascript_artifact(payload)

    def federation_status(self) -> dict[str, Any]:
        return self.federation.status()

    def register_policy(self, source: str) -> dict[str, Any]:
        return self.policy_registry.register(source)

    def transition_policy(self, *, policy_id: str, status: str) -> dict[str, Any]:
        return self.policy_registry.transition(policy_id=policy_id, status=status)

    def organization_risk_dashboard(self, *, organization_id: str) -> dict[str, Any]:
        return self.assurance_monitor.risk_dashboard(organization_id=organization_id)

    def global_trust_status(self) -> dict[str, Any]:
        return self.global_trust_network.status()

    def trust_graph(self) -> dict[str, Any]:
        return self.federation.trust_graph()

    def standard_profile_status(self) -> dict[str, Any]:
        return self.standard_profile.profile()

    def platform_integrations_status(self, *, organization_id: str) -> dict[str, Any]:
        return {
            "mode": "platform_others_plug_into",
            "organization_id": organization_id,
            "integrations": self.integrations.list(organization_id=organization_id),
        }

    def register_platform_integration(
        self,
        *,
        organization_id: str,
        integration_name: str,
        integration_type: str,
        scopes: list[str],
    ) -> dict[str, Any]:
        return self.integrations.register(
            organization_id=organization_id,
            integration_name=integration_name,
            integration_type=integration_type,
            scopes=scopes,
        )

    def field_adoption_status(self) -> dict[str, Any]:
        return self.field_adoption.status()

    def onboard_organization(
        self,
        *,
        organization_id: str,
        legal_name: str,
        sector: str,
        trust_domain: str,
    ) -> dict[str, Any]:
        adoption = self.field_adoption.onboard(
            organization_id=organization_id,
            legal_name=legal_name,
            sector=sector,
            trust_domain=trust_domain,
        )
        self.global_trust_network.join(organization_id=organization_id, trust_domain=trust_domain, trust_score=80)
        self.federation.register_organization(organization_id=organization_id, trust_domain=trust_domain, trust_score=80)
        return adoption

    def record_production_evidence(
        self,
        *,
        organization_id: str,
        project_id: str,
        environment: str,
        evidence_type: str,
        validation_status: str,
        evidence_hash: str | None = None,
    ) -> dict[str, Any]:
        return self.production_evidence.record(
            organization_id=organization_id,
            project_id=project_id,
            environment=environment,
            evidence_type=evidence_type,
            validation_status=validation_status,
            evidence_hash=evidence_hash,
        )

    def trust_exchange(
        self,
        *,
        issuer_org: str,
        subject_org: str,
        receipt_hash: str,
        trust_score: int,
    ) -> dict[str, Any]:
        return self.federation.trust_exchange(
            issuer_org=issuer_org,
            subject_org=subject_org,
            receipt_hash=receipt_hash,
            trust_score=trust_score,
        )

    def record_deployment_feedback(
        self,
        *,
        organization_id: str,
        project_id: str,
        environment: str,
        status: str,
        validation_score: int,
        evidence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self.deployment_feedback.record(
            organization_id=organization_id,
            project_id=project_id,
            environment=environment,
            status=status,
            validation_score=validation_score,
            evidence=evidence,
        )

    def public_receipt(self, receipt_id: str) -> dict[str, Any] | None:
        receipt = self.receipts.find(receipt_id)
        if receipt is None:
            return None
        return {
            "mode": "public_trust_receipt",
            "receipt": receipt,
            "verification": self.receipts.verify(receipt),
        }

    def public_certificate(self, certificate_id: str) -> dict[str, Any] | None:
        certificate = self.certificates.find_certificate(certificate_id)
        if certificate is None:
            return None
        return {
            "mode": "public_certificate_verification",
            "certificate": certificate,
            "certificate_hash": certificate.get("certificate_hash") or certificate.get("public_key_hash"),
        }

    def public_assurance_report(self, report_id: str) -> dict[str, Any] | None:
        report = self.assurance_reporter.find(report_id)
        if report is None:
            return None
        return {
            "mode": "public_assurance_report",
            "report": report,
            "verified": bool(report.get("report_hash")),
        }

    def portable_verification_package(self, receipt_id: str) -> dict[str, Any] | None:
        receipt = self.receipts.find(receipt_id)
        if receipt is None:
            return None
        chain = self.certificates.find_chain_by_receipt(receipt_id)
        if chain is None:
            return None
        assurance_report = {
            "report_id": "external-report-" + sha256(receipt_id.encode()).hexdigest()[:12],
            "report_hash": sha256(f"{receipt_id}:{chain.get('chain_hash')}".encode()).hexdigest(),
        }
        explanation = self.explainability.explain(
            decision="public_verify",
            policy_decision={"policy_id": "public-verification", "policy_version": 1, "allowed": True},
            trust={"trust_score": receipt.get("trust_score", 0)},
            certificate_chain=chain,
            assurance={"assurance_status": "assured"},
        )
        return self.verification_packager.package(
            receipt=receipt,
            certificate_chain=chain,
            assurance_report=assurance_report,
            proof={"receipt_id": receipt_id, "chain_id": chain.get("chain_id")},
            explanation=explanation,
        )


def _strip_timestamp_fields(value: Any) -> Any:
    excluded = {"created_at", "updated_at", "generated_at", "timestamp"}
    if isinstance(value, dict):
        return {
            key: _strip_timestamp_fields(item)
            for key, item in value.items()
            if key not in excluded
        }
    if isinstance(value, list):
        return [_strip_timestamp_fields(item) for item in value]
    return value


def _select_project(project_id: str | None) -> ProjectWorkspace:
    projects = {project.project_id: project for project in afroprog_seed_projects()}
    if project_id and project_id in projects:
        return projects[project_id]
    return next(iter(projects.values()))


_DEFAULT_ENGINE = NovaScriptV2Engine()


def get_novascript_v2_engine() -> NovaScriptV2Engine:
    return _DEFAULT_ENGINE
