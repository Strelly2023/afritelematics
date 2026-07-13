from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_nera_manifest() -> dict[str, Any]:
    platform_domains = [
        "NovaWorkspace",
        "NovaProjects",
        "NovaAgents",
        "NovaExecution",
        "NovaReviews",
        "NovaApprovals",
        "NovaGovernance",
        "NovaKnowledge",
        "NovaAutomation",
        "NovaTesting",
        "NovaDeployments",
        "NovaObservability",
        "NovaReporting",
        "NovaAdministration",
    ]
    enterprise_capabilities = [
        "NovaTrust",
        "NovaID",
        "NovaSecure",
        "NovaPolicy",
        "NovaRisk",
        "NovaCompliance",
        "NovaAudit",
        "NovaEvents",
        "NovaWorkflow",
        "NovaAutomation",
        "NovaKnowledge",
        "NovaGraph",
        "NovaMemory",
        "NovaInsights",
        "NovaDecision",
        "NovaDigitalTwin",
    ]
    return {
        "id": "nera",
        "name": "NovaTech Enterprise Reference Architecture",
        "version": "1.1",
        "generated_at": _now(),
        "layers": [
            {
                "id": "corporate-governance",
                "name": "Corporate Governance",
                "purpose": "Board, executive, and enterprise accountability.",
                "stable": True,
            },
            {
                "id": "enterprise-governance",
                "name": "Enterprise Governance",
                "purpose": "Identity, security, policy, risk, compliance, and audit.",
                "stable": True,
            },
            {
                "id": "enterprise-platform",
                "name": "Enterprise Platform",
                "purpose": "Reusable capabilities shared across all products.",
                "stable": True,
            },
            {
                "id": "knowledge-intelligence",
                "name": "Knowledge & Intelligence Layer",
                "purpose": "Memory, reasoning, digital twin, and decision intelligence.",
                "stable": True,
            },
            {
                "id": "business-products",
                "name": "Business Products",
                "purpose": "Customer-facing and partner-facing products.",
                "stable": False,
            },
            {
                "id": "enterprise-operations",
                "name": "Enterprise Operations",
                "purpose": "Run-the-business operations and support functions.",
                "stable": False,
            },
            {
                "id": "shared-enterprise-services",
                "name": "Shared Enterprise Services",
                "purpose": "Common services consumed by every product and platform domain.",
                "stable": True,
            },
            {
                "id": "infrastructure",
                "name": "Infrastructure",
                "purpose": "Cloud, networking, runtime, storage, and edge services.",
                "stable": True,
            },
        ],
        "enterprise_platform": {
            "domains": platform_domains,
            "shared_capabilities": enterprise_capabilities,
            "default_ai_layer": "NovaAI",
        },
        "knowledge_and_intelligence": {
            "services": [
                "NovaKnowledge",
                "NovaGraph",
                "NovaMemory",
                "NovaDecision",
                "NovaInsights",
                "NovaDigitalTwin",
                "NovaSearch",
                "NovaLearning",
            ],
            "graph_relationships": [
                "Project -> Requirement",
                "Requirement -> ADR",
                "ADR -> Architecture",
                "Architecture -> Approval",
                "Approval -> Deployment",
                "Deployment -> Evidence",
            ],
        },
        "governance_chain": ["NovaPolicy", "NovaRisk", "NovaCompliance", "NovaAudit"],
        "default_product_examples": ["NovaRide", "NovaPay", "NovaHealth", "NovaCommerce"],
        "principles": [
            "Governance is persistent",
            "Platform is reusable",
            "Knowledge is cumulative",
            "Products are modular",
            "Operations are observable",
            "AI is governed",
            "Events are the integration backbone",
            "Digital twin is the enterprise intelligence layer",
        ],
        "notes": [
            "Knowledge Graph is a projection, not the source of truth.",
            "Products may be replaced without changing the enterprise platform.",
            "Governance, identity, and audit remain stable across products and regions.",
        ],
    }


def build_enterprise_capability_model() -> dict[str, Any]:
    return {
        "id": "necm",
        "name": "NovaTech Enterprise Capability Model",
        "version": "1.0",
        "generated_at": _now(),
        "capabilities": [
            "Identity",
            "Security",
            "Payments",
            "Mobility",
            "Commerce",
            "Healthcare",
            "Education",
            "Agriculture",
            "Workflow",
            "Approvals",
            "AI",
            "Knowledge",
            "Analytics",
            "Observability",
            "Compliance",
            "Risk",
            "Audit",
        ],
        "capability_groups": [
            {"name": "Customer", "items": ["Payments", "Mobility", "Commerce", "Healthcare", "Education", "Agriculture"]},
            {"name": "Platform", "items": ["Identity", "Security", "Workflow", "AI", "Knowledge", "Analytics"]},
            {"name": "Governance", "items": ["Approvals", "Compliance", "Risk", "Audit", "Observability"]},
        ],
        "product_to_capability_examples": {
            "NovaRide": ["Mobility", "Identity", "Approvals", "Observability"],
            "NovaPay": ["Payments", "Security", "Risk", "Audit"],
            "NovaHealth": ["Healthcare", "Compliance", "Identity"],
            "NovaCommerce": ["Commerce", "Workflow", "Analytics"],
        },
    }


def build_enterprise_operating_model() -> dict[str, Any]:
    return {
        "id": "neom",
        "name": "NovaTech Enterprise Operating Model",
        "version": "1.0",
        "generated_at": _now(),
        "people": ["Executives", "Product Managers", "Engineers", "Analysts", "Operators", "Legal", "Compliance"],
        "roles": ["Owner", "Steward", "Approver", "Operator", "Agent", "Reviewer"],
        "departments": ["Engineering", "Product", "Operations", "Finance", "HR", "Legal", "Security", "Data"],
        "workspaces": ["NovaCodePro", "Customer Platforms", "Partner Platforms", "Enterprise Analytics"],
        "processes": ["Intake", "Review", "Approval", "Execution", "Monitoring", "Learning"],
        "ai_agents": ["Architect Agent", "Developer Agent", "QA Agent", "Security Agent", "Compliance Agent"],
    }


def build_enterprise_meta_model() -> dict[str, Any]:
    return {
        "id": "enterprise-meta-model",
        "name": "NovaTech Enterprise Meta Model",
        "version": "1.0",
        "generated_at": _now(),
        "entities": [
            "Organization",
            "Business Unit",
            "Department",
            "Team",
            "Workspace",
            "Project",
            "Product",
            "Service",
            "Capability",
            "Policy",
            "Risk",
            "Approval",
            "Deployment",
            "Event",
            "Evidence",
            "Knowledge",
            "Agent",
            "User",
            "Identity",
            "Digital Twin",
        ],
        "relationships": [
            "Organization owns Product",
            "Product consumes Capability",
            "Workspace contains Project",
            "Project produces Event",
            "Event updates Digital Twin",
            "Approval governs Deployment",
            "Evidence supports Approval",
            "Knowledge links to Policy",
        ],
    }


def build_enterprise_data_architecture() -> dict[str, Any]:
    return {
        "id": "nedm",
        "name": "NovaTech Enterprise Data Model",
        "version": "1.0",
        "generated_at": _now(),
        "layers": [
            "Operational Database",
            "Event Store",
            "Knowledge Graph",
            "Enterprise Memory",
            "Digital Twin",
        ],
        "flow": [
            "Operational Database -> Event Store",
            "Event Store -> Knowledge Graph",
            "Knowledge Graph -> Enterprise Memory",
            "Enterprise Memory -> Digital Twin",
            "Digital Twin -> AI Reasoning",
        ],
        "notes": [
            "Operational databases remain the source of record.",
            "Knowledge graphs are projections.",
            "Digital twin is the current enterprise state.",
        ],
    }


def build_enterprise_ai_architecture() -> dict[str, Any]:
    return {
        "id": "nai",
        "name": "NovaTech Enterprise AI Architecture",
        "version": "1.0",
        "generated_at": _now(),
        "stack": [
            "Agent Registry",
            "Agent Identity",
            "Agent Governance",
            "Agent Marketplace",
            "Agent Memory",
            "Agent Orchestrator",
            "Agent Runtime",
            "Agent Monitoring",
            "Agent Analytics",
            "Agent Learning",
            "Agent SDK",
        ],
        "governance": [
            "Authenticate through NovaID",
            "Authorize through NovaPolicy",
            "Record evidence in NovaAudit",
            "Publish knowledge to NovaKnowledge",
            "Communicate through NovaEvents",
        ],
    }


def build_enterprise_digital_twin_model() -> dict[str, Any]:
    return {
        "id": "ndtm",
        "name": "NovaTech Enterprise Digital Twin Model",
        "version": "1.0",
        "generated_at": _now(),
        "twin_domains": [
            "Organization",
            "People",
            "Product",
            "Service",
            "Infrastructure",
            "Network",
            "Policy",
            "Risk",
            "Security",
            "Financial",
            "Knowledge",
            "Operations",
            "AI",
        ],
        "capabilities": [
            "Current state",
            "Scenario simulation",
            "Impact analysis",
            "Recovery validation",
            "RTO/RPO analysis",
            "Cascading failure analysis",
        ],
    }


def build_enterprise_architecture_framework() -> dict[str, Any]:
    return {
        "id": "natech-framework",
        "name": "NovaTech Enterprise Architecture Framework",
        "version": "1.0",
        "generated_at": _now(),
        "models": {
            "nera": build_nera_manifest(),
            "necm": build_enterprise_capability_model(),
            "neom": build_enterprise_operating_model(),
            "nedm": build_enterprise_data_architecture(),
            "nekm": build_enterprise_meta_model(),
            "nai": build_enterprise_ai_architecture(),
            "ndtm": build_enterprise_digital_twin_model(),
        },
    }


__all__ = [
    "build_nera_manifest",
    "build_enterprise_architecture_framework",
    "build_enterprise_capability_model",
    "build_enterprise_operating_model",
    "build_enterprise_meta_model",
    "build_enterprise_data_architecture",
    "build_enterprise_ai_architecture",
    "build_enterprise_digital_twin_model",
]
