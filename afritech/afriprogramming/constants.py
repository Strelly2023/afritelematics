"""Constitutional constants for the AfriProgramming engineering pillar."""

from __future__ import annotations

from typing import Dict, Tuple


AFRIPROGRAMMING_COMPONENT = "AfriProgramming"
AFRIPROGRAMMING_COMPONENT_ID = "afritech.afriprogramming"
AFRIPROGRAMMING_PILLAR = "ENGINEERING"
AFRIPROGRAMMING_STATUS = "GA_ELITE_AUTONOMOUS_ENGINEERING_PLATFORM"
AFRIPROGRAMMING_VERSION = "1.0"

QUESTION_ANSWERED = "How do we build it?"
PURPOSE = "Builds and verifies software systems."
CANONICAL_DEFINITION = (
    "AfriProgramming is a proof-aware autonomous engineering platform that "
    "combines AI software agents, software lifecycle automation, verification, "
    "testing, constitutional governance, and engineering intelligence to build, "
    "validate, and evolve intelligent software systems."
)

GOVERNANCE_AUTHORITY = False
PROOF_AUTHORITY = False
REPLAY_AUTHORITY = False
CI_AUTHORITY = False
ADMISSIBILITY_AUTHORITY = False
INTELLIGENCE_AUTHORITY = False
EXECUTION_AUTHORITY = False
POLICY_AUTHORITY = False
CONSTITUTIONAL_AUTHORITY = False

ENGINEERING_PILLAR = True
AUTONOMOUS_ENGINEERING_AGENT = True
MULTI_AGENT_ENGINEERING = True
CODEBASE_INTELLIGENCE = True
AUTONOMOUS_SDLC = True
PROOF_AWARE_ENGINEERING = True
CONSTITUTIONAL_ENGINEERING = True
SOFTWARE_VERIFICATION = True
TESTING_PLATFORM = True
SANDBOX_EXECUTION = True
PULL_REQUEST_INTELLIGENCE = True
DEVELOPER_WORKSPACE = True
AGENT_SKILLS_MARKETPLACE = True
SECURITY_ENGINEERING = True
EXPLAINABLE_ENGINEERING = True
KNOWLEDGE_GRAPH_ENGINEERING = True
ENTERPRISE_PORTFOLIO_MANAGEMENT = True
AFRITECH_ECOSYSTEM_INTEGRATION = True

MUTATION_ALLOWED = False
PROOF_MUTATION_ALLOWED = False
REPLAY_MUTATION_ALLOWED = False
GOVERNANCE_MUTATION_ALLOWED = False
AUTHORITY_ESCALATION_ALLOWED = False

MODEL_CLASSIFICATION = "AUTONOMOUS_ENGINEERING_MODEL"
ARTIFACT_CLASSIFICATION = "ENGINEERING_ARTIFACT"
OUTPUT_CLASSIFICATION = "SOFTWARE_ENGINEERING_VIEW"

AGENT_ROLES: Tuple[str, ...] = (
    "architecture",
    "backend",
    "frontend",
    "testing",
    "security",
    "documentation",
    "devops",
    "codebase_intelligence",
)

LIFECYCLE_STAGES: Tuple[str, ...] = (
    "requirements",
    "design",
    "build",
    "verify",
    "deploy",
    "operate",
)

FEATURE_GROUPS: Tuple[str, ...] = (
    "Autonomous Engineering Agent",
    "Multi-Agent Engineering",
    "Codebase Intelligence",
    "Autonomous Software Development Lifecycle",
    "Proof-Aware Engineering",
    "Constitutional Engineering",
    "Software Verification",
    "Testing Platform",
    "Sandbox Execution",
    "Pull Request Intelligence",
    "Developer Workspace",
    "Agent Skills Marketplace",
    "Security Engineering",
    "Explainable Engineering",
    "Knowledge Graph Engineering",
    "Enterprise Portfolio Management",
    "AfriTech Ecosystem Integration",
)

CAPABILITIES: Tuple[str, ...] = (
    "natural_language_to_software",
    "requirements_to_implementation",
    "autonomous_feature_development",
    "autonomous_bug_fixing",
    "autonomous_refactoring",
    "autonomous_code_review",
    "autonomous_documentation",
    "autonomous_test_generation",
    "autonomous_pull_request_generation",
    "parallel_engineering_agents",
    "repository_understanding",
    "dependency_analysis",
    "architecture_understanding",
    "impact_analysis",
    "technical_debt_detection",
    "knowledge_graph_generation",
    "brd_generation",
    "srs_generation",
    "user_story_generation",
    "sad_generation",
    "sdd_generation",
    "adr_generation",
    "data_model_generation",
    "api_specification_generation",
    "code_generation",
    "test_generation",
    "documentation_generation",
    "validation",
    "release_governance",
    "claim_evidence_mapping",
    "proof_artifact_generation",
    "witness_generation",
    "verification_receipts",
    "traceability",
    "invariant_enforcement",
    "rule_enforcement",
    "binding_enforcement",
    "guard_enforcement",
    "static_analysis",
    "architecture_validation",
    "dependency_validation",
    "security_validation",
    "compliance_validation",
    "runtime_validation",
    "unit_testing",
    "integration_testing",
    "contract_testing",
    "api_testing",
    "e2e_testing",
    "regression_testing",
    "performance_testing",
    "security_testing",
    "isolated_execution_environments",
    "safe_experimentation",
    "pr_explanation",
    "pr_review",
    "pr_validation",
    "merge_recommendations",
    "ide_integration",
    "git_integration",
    "repository_integration",
    "local_cli",
    "web_workspace",
    "reusable_agent_skills",
    "engineering_playbooks",
    "organizational_standards",
    "secure_code_review",
    "vulnerability_detection",
    "dependency_scanning",
    "threat_modeling",
    "engineering_explainability",
    "architecture_graph",
    "dependency_graph",
    "adr_graph",
    "capability_graph",
    "governance_graph",
    "multi_project_management",
    "program_management",
    "portfolio_management",
    "engineering_kpis",
    "delivery_metrics",
    "africppt_governance_integration",
    "afritpps_execution_integration",
    "afripower_intelligence_integration",
)

ARTIFACT_TYPES: Tuple[str, ...] = (
    "BRD",
    "SRS",
    "USER_STORY",
    "EPIC",
    "USE_CASE",
    "SAD",
    "SDD",
    "ADR",
    "DATA_MODEL",
    "API_SPEC",
    "CODE",
    "TEST",
    "DOCUMENTATION",
    "VALIDATION",
    "COMPLIANCE",
    "RELEASE_GOVERNANCE",
    "PROOF_ARTIFACT",
    "WITNESS",
    "VERIFICATION_RECEIPT",
    "TRACEABILITY_REPORT",
    "PR_EXPLANATION",
    "KNOWLEDGE_GRAPH",
    "PORTFOLIO_METRICS",
)

OUTPUTS: Tuple[str, ...] = (
    "Code",
    "Tests",
    "Validators",
    "Runtime Systems",
    "Proof Artifacts",
    "Software Platforms",
)

CONSTITUTIONAL_STATEMENT = (
    "AfriProgramming engineers systems. It turns intent into code, tests, "
    "validators, runtime systems, proof artifacts, and software platforms "
    "through autonomous agents, lifecycle automation, verification, testing, "
    "constitutional governance integration, explainability, and engineering "
    "intelligence without creating governance, proof, replay, CI, "
    "admissibility, execution, or intelligence authority."
)


def constitutional_afriprogramming_metadata() -> Dict[str, object]:
    return {
        "component": AFRIPROGRAMMING_COMPONENT,
        "component_id": AFRIPROGRAMMING_COMPONENT_ID,
        "pillar": AFRIPROGRAMMING_PILLAR,
        "status": AFRIPROGRAMMING_STATUS,
        "version": AFRIPROGRAMMING_VERSION,
        "purpose": PURPOSE,
        "question_answered": QUESTION_ANSWERED,
        "canonical_definition": CANONICAL_DEFINITION,
        "feature_groups": FEATURE_GROUPS,
        "outputs": OUTPUTS,
        "model_classification": MODEL_CLASSIFICATION,
        "artifact_classification": ARTIFACT_CLASSIFICATION,
        "output_classification": OUTPUT_CLASSIFICATION,
        "engineering_pillar": ENGINEERING_PILLAR,
        "autonomous_engineering_agent": AUTONOMOUS_ENGINEERING_AGENT,
        "multi_agent_engineering": MULTI_AGENT_ENGINEERING,
        "codebase_intelligence": CODEBASE_INTELLIGENCE,
        "autonomous_sdlc": AUTONOMOUS_SDLC,
        "proof_aware_engineering": PROOF_AWARE_ENGINEERING,
        "constitutional_engineering": CONSTITUTIONAL_ENGINEERING,
        "software_verification": SOFTWARE_VERIFICATION,
        "testing_platform": TESTING_PLATFORM,
        "sandbox_execution": SANDBOX_EXECUTION,
        "pull_request_intelligence": PULL_REQUEST_INTELLIGENCE,
        "developer_workspace": DEVELOPER_WORKSPACE,
        "agent_skills_marketplace": AGENT_SKILLS_MARKETPLACE,
        "security_engineering": SECURITY_ENGINEERING,
        "explainable_engineering": EXPLAINABLE_ENGINEERING,
        "knowledge_graph_engineering": KNOWLEDGE_GRAPH_ENGINEERING,
        "enterprise_portfolio_management": ENTERPRISE_PORTFOLIO_MANAGEMENT,
        "afritech_ecosystem_integration": AFRITECH_ECOSYSTEM_INTEGRATION,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "policy_authority": POLICY_AUTHORITY,
        "constitutional_authority": CONSTITUTIONAL_AUTHORITY,
        "mutation_allowed": MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "replay_mutation_allowed": REPLAY_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "authority_escalation_allowed": AUTHORITY_ESCALATION_ALLOWED,
        "constitutional_statement": CONSTITUTIONAL_STATEMENT,
    }


def assert_afriprogramming_constitution() -> None:
    forbidden_authority_flags = (
        GOVERNANCE_AUTHORITY,
        PROOF_AUTHORITY,
        REPLAY_AUTHORITY,
        CI_AUTHORITY,
        ADMISSIBILITY_AUTHORITY,
        INTELLIGENCE_AUTHORITY,
        EXECUTION_AUTHORITY,
        POLICY_AUTHORITY,
        CONSTITUTIONAL_AUTHORITY,
        MUTATION_ALLOWED,
        PROOF_MUTATION_ALLOWED,
        REPLAY_MUTATION_ALLOWED,
        GOVERNANCE_MUTATION_ALLOWED,
        AUTHORITY_ESCALATION_ALLOWED,
    )

    if any(forbidden_authority_flags):
        raise RuntimeError("AfriProgramming authority boundary violation detected")

    required_engineering_flags = (
        ENGINEERING_PILLAR,
        AUTONOMOUS_ENGINEERING_AGENT,
        MULTI_AGENT_ENGINEERING,
        CODEBASE_INTELLIGENCE,
        AUTONOMOUS_SDLC,
        PROOF_AWARE_ENGINEERING,
        CONSTITUTIONAL_ENGINEERING,
        SOFTWARE_VERIFICATION,
        TESTING_PLATFORM,
        SANDBOX_EXECUTION,
        PULL_REQUEST_INTELLIGENCE,
        DEVELOPER_WORKSPACE,
        AGENT_SKILLS_MARKETPLACE,
        SECURITY_ENGINEERING,
        EXPLAINABLE_ENGINEERING,
        KNOWLEDGE_GRAPH_ENGINEERING,
        ENTERPRISE_PORTFOLIO_MANAGEMENT,
        AFRITECH_ECOSYSTEM_INTEGRATION,
    )

    if not all(required_engineering_flags):
        raise RuntimeError("AfriProgramming GA Elite capability violation detected")


__all__ = [
    "AFRIPROGRAMMING_COMPONENT",
    "AFRIPROGRAMMING_COMPONENT_ID",
    "AFRIPROGRAMMING_PILLAR",
    "AFRIPROGRAMMING_STATUS",
    "AFRIPROGRAMMING_VERSION",
    "QUESTION_ANSWERED",
    "PURPOSE",
    "CANONICAL_DEFINITION",
    "AGENT_ROLES",
    "LIFECYCLE_STAGES",
    "FEATURE_GROUPS",
    "CAPABILITIES",
    "ARTIFACT_TYPES",
    "OUTPUTS",
    "constitutional_afriprogramming_metadata",
    "assert_afriprogramming_constitution",
]
