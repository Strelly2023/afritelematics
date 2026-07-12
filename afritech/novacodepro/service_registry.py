from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NovaCodeProServiceDefinition:
    name: str
    app_name: str
    title: str
    db_env_var: str
    database_url_env_var: str
    async_agents: bool = False
    worker_mode: str = "outbox"


SERVICE_DEFINITIONS: tuple[NovaCodeProServiceDefinition, ...] = (
    NovaCodeProServiceDefinition(
        name="gateway",
        app_name="gateway_app",
        title="NovaCodePro Gateway",
        db_env_var="NOVACODEPRO_GATEWAY_DB_PATH",
        database_url_env_var="NOVACODEPRO_GATEWAY_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="identity-context",
        app_name="identity_context_app",
        title="NovaCodePro Identity Context Service",
        db_env_var="NOVACODEPRO_IDENTITY_CONTEXT_DB_PATH",
        database_url_env_var="NOVACODEPRO_IDENTITY_CONTEXT_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="tenant",
        app_name="tenant_app",
        title="NovaCodePro Tenant Service",
        db_env_var="NOVACODEPRO_TENANT_DB_PATH",
        database_url_env_var="NOVACODEPRO_TENANT_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="federation",
        app_name="federation_app",
        title="NovaCodePro Federation Service",
        db_env_var="NOVACODEPRO_FEDERATION_DB_PATH",
        database_url_env_var="NOVACODEPRO_FEDERATION_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="solution",
        app_name="solution_app",
        title="NovaCodePro Solution Service",
        db_env_var="NOVACODEPRO_SOLUTION_DB_PATH",
        database_url_env_var="NOVACODEPRO_SOLUTION_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="workflow",
        app_name="workflow_app",
        title="NovaCodePro Workflow Service",
        db_env_var="NOVACODEPRO_WORKFLOW_DB_PATH",
        database_url_env_var="NOVACODEPRO_WORKFLOW_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="approval",
        app_name="approval_app",
        title="NovaCodePro Approval Service",
        db_env_var="NOVACODEPRO_APPROVAL_DB_PATH",
        database_url_env_var="NOVACODEPRO_APPROVAL_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="agent",
        app_name="agent_app",
        title="NovaCodePro Agent Orchestrator",
        db_env_var="NOVACODEPRO_AGENT_DB_PATH",
        database_url_env_var="NOVACODEPRO_AGENT_DATABASE_URL",
        async_agents=True,
        worker_mode="agents",
    ),
    NovaCodeProServiceDefinition(
        name="evidence",
        app_name="evidence_app",
        title="NovaCodePro Evidence Service",
        db_env_var="NOVACODEPRO_EVIDENCE_DB_PATH",
        database_url_env_var="NOVACODEPRO_EVIDENCE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="risk",
        app_name="risk_app",
        title="NovaCodePro Risk Service",
        db_env_var="NOVACODEPRO_RISK_DB_PATH",
        database_url_env_var="NOVACODEPRO_RISK_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="policy",
        app_name="policy_app",
        title="NovaCodePro Policy Service",
        db_env_var="NOVACODEPRO_POLICY_DB_PATH",
        database_url_env_var="NOVACODEPRO_POLICY_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="knowledge",
        app_name="knowledge_app",
        title="NovaCodePro Knowledge Graph Service",
        db_env_var="NOVACODEPRO_KNOWLEDGE_DB_PATH",
        database_url_env_var="NOVACODEPRO_KNOWLEDGE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="graph",
        app_name="knowledge_app",
        title="NovaCodePro Graph Service",
        db_env_var="NOVACODEPRO_KNOWLEDGE_DB_PATH",
        database_url_env_var="NOVACODEPRO_KNOWLEDGE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="digital-twin",
        app_name="digital_twin_app",
        title="NovaCodePro Digital Twin Service",
        db_env_var="NOVACODEPRO_DIGITAL_TWIN_DB_PATH",
        database_url_env_var="NOVACODEPRO_DIGITAL_TWIN_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="release",
        app_name="release_app",
        title="NovaCodePro Release Service",
        db_env_var="NOVACODEPRO_RELEASE_DB_PATH",
        database_url_env_var="NOVACODEPRO_RELEASE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="deployment",
        app_name="deployment_app",
        title="NovaCodePro Deployment Service",
        db_env_var="NOVACODEPRO_DEPLOYMENT_DB_PATH",
        database_url_env_var="NOVACODEPRO_DEPLOYMENT_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="marketplace",
        app_name="marketplace_app",
        title="NovaCodePro Marketplace Service",
        db_env_var="NOVACODEPRO_MARKETPLACE_DB_PATH",
        database_url_env_var="NOVACODEPRO_MARKETPLACE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="observability",
        app_name="observability_app",
        title="NovaCodePro Observability Service",
        db_env_var="NOVACODEPRO_OBSERVABILITY_DB_PATH",
        database_url_env_var="NOVACODEPRO_OBSERVABILITY_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="sre",
        app_name="observability_app",
        title="NovaCodePro SRE Service",
        db_env_var="NOVACODEPRO_OBSERVABILITY_DB_PATH",
        database_url_env_var="NOVACODEPRO_OBSERVABILITY_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="incident",
        app_name="incident_app",
        title="NovaCodePro Incident Service",
        db_env_var="NOVACODEPRO_INCIDENT_DB_PATH",
        database_url_env_var="NOVACODEPRO_INCIDENT_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="command-center",
        app_name="command_center_app",
        title="NovaCodePro Command Center Service",
        db_env_var="NOVACODEPRO_COMMAND_CENTER_DB_PATH",
        database_url_env_var="NOVACODEPRO_COMMAND_CENTER_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="board-governance",
        app_name="board_governance_app",
        title="NovaCodePro Board Governance Service",
        db_env_var="NOVACODEPRO_BOARD_GOVERNANCE_DB_PATH",
        database_url_env_var="NOVACODEPRO_BOARD_GOVERNANCE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="board",
        app_name="board_governance_app",
        title="NovaCodePro Board Governance Service",
        db_env_var="NOVACODEPRO_BOARD_GOVERNANCE_DB_PATH",
        database_url_env_var="NOVACODEPRO_BOARD_GOVERNANCE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="executive",
        app_name="executive_app",
        title="NovaCodePro Executive Intelligence Service",
        db_env_var="NOVACODEPRO_EXECUTIVE_DB_PATH",
        database_url_env_var="NOVACODEPRO_EXECUTIVE_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="audit",
        app_name="audit_app",
        title="NovaCodePro Audit Service",
        db_env_var="NOVACODEPRO_AUDIT_DB_PATH",
        database_url_env_var="NOVACODEPRO_AUDIT_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="event-mesh",
        app_name="audit_app",
        title="NovaCodePro Event Mesh Service",
        db_env_var="NOVACODEPRO_AUDIT_DB_PATH",
        database_url_env_var="NOVACODEPRO_AUDIT_DATABASE_URL",
    ),
    NovaCodeProServiceDefinition(
        name="notification",
        app_name="notification_app",
        title="NovaCodePro Notification Service",
        db_env_var="NOVACODEPRO_NOTIFICATION_DB_PATH",
        database_url_env_var="NOVACODEPRO_NOTIFICATION_DATABASE_URL",
    ),
)


def service_definition_map() -> dict[str, NovaCodeProServiceDefinition]:
    return {definition.name: definition for definition in SERVICE_DEFINITIONS}


def get_service_definition(name: str) -> NovaCodeProServiceDefinition:
    definitions = service_definition_map()
    if name not in definitions:
        raise KeyError(f"Unknown NovaCodePro service: {name}")
    return definitions[name]
