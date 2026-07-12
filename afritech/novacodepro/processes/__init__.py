from __future__ import annotations

from afritech.novacodepro.distributed.process import build_process_app

gateway_app = build_process_app(
    service_name="gateway",
    db_env_var="NOVACODEPRO_GATEWAY_DB_PATH",
    title="NovaCodePro Gateway",
)
identity_context_app = build_process_app(
    service_name="identity-context",
    db_env_var="NOVACODEPRO_IDENTITY_CONTEXT_DB_PATH",
    title="NovaCodePro Identity Context Service",
)
tenant_app = build_process_app(
    service_name="tenant",
    db_env_var="NOVACODEPRO_TENANT_DB_PATH",
    title="NovaCodePro Tenant Service",
)
federation_app = build_process_app(
    service_name="federation",
    db_env_var="NOVACODEPRO_FEDERATION_DB_PATH",
    title="NovaCodePro Federation Service",
)
solution_app = build_process_app(
    service_name="solution",
    db_env_var="NOVACODEPRO_SOLUTION_DB_PATH",
    title="NovaCodePro Solution Service",
)
workflow_app = build_process_app(
    service_name="workflow",
    db_env_var="NOVACODEPRO_WORKFLOW_DB_PATH",
    title="NovaCodePro Workflow Service",
)
approval_app = build_process_app(
    service_name="approval",
    db_env_var="NOVACODEPRO_APPROVAL_DB_PATH",
    title="NovaCodePro Approval Service",
)
agent_app = build_process_app(
    service_name="agent",
    db_env_var="NOVACODEPRO_AGENT_DB_PATH",
    title="NovaCodePro Agent Orchestrator",
    async_agents=True,
)
evidence_app = build_process_app(
    service_name="evidence",
    db_env_var="NOVACODEPRO_EVIDENCE_DB_PATH",
    title="NovaCodePro Evidence Service",
)
risk_app = build_process_app(
    service_name="risk",
    db_env_var="NOVACODEPRO_RISK_DB_PATH",
    title="NovaCodePro Risk Service",
)
policy_app = build_process_app(
    service_name="policy",
    db_env_var="NOVACODEPRO_POLICY_DB_PATH",
    title="NovaCodePro Policy Service",
)
knowledge_app = build_process_app(
    service_name="knowledge",
    db_env_var="NOVACODEPRO_KNOWLEDGE_DB_PATH",
    title="NovaCodePro Knowledge Graph Service",
)
digital_twin_app = build_process_app(
    service_name="digital-twin",
    db_env_var="NOVACODEPRO_DIGITAL_TWIN_DB_PATH",
    title="NovaCodePro Digital Twin Service",
)
release_app = build_process_app(
    service_name="release",
    db_env_var="NOVACODEPRO_RELEASE_DB_PATH",
    title="NovaCodePro Release Service",
)
deployment_app = build_process_app(
    service_name="deployment",
    db_env_var="NOVACODEPRO_DEPLOYMENT_DB_PATH",
    title="NovaCodePro Deployment Service",
)
marketplace_app = build_process_app(
    service_name="marketplace",
    db_env_var="NOVACODEPRO_MARKETPLACE_DB_PATH",
    title="NovaCodePro Marketplace Service",
)
observability_app = build_process_app(
    service_name="observability",
    db_env_var="NOVACODEPRO_OBSERVABILITY_DB_PATH",
    title="NovaCodePro Observability Service",
)
incident_app = build_process_app(
    service_name="incident",
    db_env_var="NOVACODEPRO_INCIDENT_DB_PATH",
    title="NovaCodePro Incident Service",
)
command_center_app = build_process_app(
    service_name="command-center",
    db_env_var="NOVACODEPRO_COMMAND_CENTER_DB_PATH",
    title="NovaCodePro Command Center Service",
)
board_governance_app = build_process_app(
    service_name="board-governance",
    db_env_var="NOVACODEPRO_BOARD_GOVERNANCE_DB_PATH",
    title="NovaCodePro Board Governance Service",
)
executive_app = build_process_app(
    service_name="executive",
    db_env_var="NOVACODEPRO_EXECUTIVE_DB_PATH",
    title="NovaCodePro Executive Intelligence Service",
)
audit_app = build_process_app(
    service_name="audit",
    db_env_var="NOVACODEPRO_AUDIT_DB_PATH",
    title="NovaCodePro Audit Service",
)
notification_app = build_process_app(
    service_name="notification",
    db_env_var="NOVACODEPRO_NOTIFICATION_DB_PATH",
    title="NovaCodePro Notification Service",
)

__all__ = [
    "agent_app",
    "approval_app",
    "audit_app",
    "board_governance_app",
    "command_center_app",
    "deployment_app",
    "digital_twin_app",
    "evidence_app",
    "executive_app",
    "federation_app",
    "gateway_app",
    "incident_app",
    "identity_context_app",
    "knowledge_app",
    "marketplace_app",
    "notification_app",
    "observability_app",
    "policy_app",
    "release_app",
    "risk_app",
    "solution_app",
    "tenant_app",
    "workflow_app",
]
