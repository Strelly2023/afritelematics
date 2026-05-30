"""Constitutional constants for the AfriTPPS execution pillar."""

from __future__ import annotations

from typing import Dict, Tuple


AFRITPPS_COMPONENT = "AfriTPPS"
AFRITPPS_COMPONENT_ID = "afritech.afritpps"
AFRITPPS_PILLAR = "EXECUTION"
AFRITPPS_STATUS = "GA_ELITE_EXECUTION_PILLAR"
AFRITPPS_VERSION = "1.0"

QUESTION_ANSWERED = "How should it be executed?"
PURPOSE = "Defines how work gets executed."

GOVERNANCE_AUTHORITY = False
PROOF_AUTHORITY = False
REPLAY_AUTHORITY = False
CI_AUTHORITY = False
ADMISSIBILITY_AUTHORITY = False
INTELLIGENCE_AUTHORITY = False
ENGINEERING_AUTHORITY = False
POLICY_AUTHORITY = False
CONSTITUTIONAL_AUTHORITY = False

EXECUTION_PILLAR = True
OPERATIONAL_CAPABILITY = True
WORKFLOW_ORCHESTRATION = True
PROCESS_EXECUTION = True
PROGRAM_EXECUTION = True
PERFORMANCE_MANAGEMENT = True
CAPABILITY_MATURITY = True

MUTATION_ALLOWED = False
PROOF_MUTATION_ALLOWED = False
REPLAY_MUTATION_ALLOWED = False
GOVERNANCE_MUTATION_ALLOWED = False
AUTHORITY_ESCALATION_ALLOWED = False

MODEL_CLASSIFICATION = "OPERATIONAL_EXECUTION_MODEL"
METRIC_CLASSIFICATION = "EXECUTION_METRIC"
OUTPUT_CLASSIFICATION = "CAPABILITY_EXECUTION_VIEW"

CAPABILITY_TYPES: Tuple[str, ...] = (
    "technology",
    "process",
    "people",
    "skills",
    "service",
    "program",
)

MATURITY_LEVELS: Tuple[str, ...] = (
    "initial",
    "managed",
    "defined",
    "measured",
    "optimized",
)

WORKFLOW_STEP_STATUSES: Tuple[str, ...] = (
    "planned",
    "ready",
    "executing",
    "blocked",
    "complete",
)

EXECUTION_METRIC_TYPES: Tuple[str, ...] = (
    "readiness_score",
    "workflow_count",
    "capability_count",
    "cycle_time",
    "throughput",
    "sla_attainment",
    "quality_score",
    "risk_score",
)

OUTPUTS: Tuple[str, ...] = (
    "Capabilities",
    "Workflows",
    "Processes",
    "Programs",
    "Operational Models",
    "Execution Metrics",
)

CONSTITUTIONAL_STATEMENT = (
    "AfriTPPS executes capability. It defines operational capability, "
    "process execution, workflow orchestration, delivery management, "
    "service operations, program execution, capability maturity, and "
    "performance management without creating governance, replay, proof, "
    "CI, admissibility, intelligence, or engineering authority."
)


def constitutional_afritpps_metadata() -> Dict[str, object]:
    return {
        "component": AFRITPPS_COMPONENT,
        "component_id": AFRITPPS_COMPONENT_ID,
        "pillar": AFRITPPS_PILLAR,
        "status": AFRITPPS_STATUS,
        "version": AFRITPPS_VERSION,
        "purpose": PURPOSE,
        "question_answered": QUESTION_ANSWERED,
        "outputs": OUTPUTS,
        "model_classification": MODEL_CLASSIFICATION,
        "metric_classification": METRIC_CLASSIFICATION,
        "output_classification": OUTPUT_CLASSIFICATION,
        "execution_pillar": EXECUTION_PILLAR,
        "operational_capability": OPERATIONAL_CAPABILITY,
        "workflow_orchestration": WORKFLOW_ORCHESTRATION,
        "process_execution": PROCESS_EXECUTION,
        "program_execution": PROGRAM_EXECUTION,
        "performance_management": PERFORMANCE_MANAGEMENT,
        "capability_maturity": CAPABILITY_MATURITY,
        "governance_authority": GOVERNANCE_AUTHORITY,
        "proof_authority": PROOF_AUTHORITY,
        "replay_authority": REPLAY_AUTHORITY,
        "ci_authority": CI_AUTHORITY,
        "admissibility_authority": ADMISSIBILITY_AUTHORITY,
        "intelligence_authority": INTELLIGENCE_AUTHORITY,
        "engineering_authority": ENGINEERING_AUTHORITY,
        "policy_authority": POLICY_AUTHORITY,
        "constitutional_authority": CONSTITUTIONAL_AUTHORITY,
        "mutation_allowed": MUTATION_ALLOWED,
        "proof_mutation_allowed": PROOF_MUTATION_ALLOWED,
        "replay_mutation_allowed": REPLAY_MUTATION_ALLOWED,
        "governance_mutation_allowed": GOVERNANCE_MUTATION_ALLOWED,
        "authority_escalation_allowed": AUTHORITY_ESCALATION_ALLOWED,
        "constitutional_statement": CONSTITUTIONAL_STATEMENT,
    }


def assert_afritpps_constitution() -> None:
    forbidden_authority_flags = (
        GOVERNANCE_AUTHORITY,
        PROOF_AUTHORITY,
        REPLAY_AUTHORITY,
        CI_AUTHORITY,
        ADMISSIBILITY_AUTHORITY,
        INTELLIGENCE_AUTHORITY,
        ENGINEERING_AUTHORITY,
        POLICY_AUTHORITY,
        CONSTITUTIONAL_AUTHORITY,
        MUTATION_ALLOWED,
        PROOF_MUTATION_ALLOWED,
        REPLAY_MUTATION_ALLOWED,
        GOVERNANCE_MUTATION_ALLOWED,
        AUTHORITY_ESCALATION_ALLOWED,
    )

    if any(forbidden_authority_flags):
        raise RuntimeError("AfriTPPS authority boundary violation detected")

    required_execution_flags = (
        EXECUTION_PILLAR,
        OPERATIONAL_CAPABILITY,
        WORKFLOW_ORCHESTRATION,
        PROCESS_EXECUTION,
        PROGRAM_EXECUTION,
        PERFORMANCE_MANAGEMENT,
        CAPABILITY_MATURITY,
    )

    if not all(required_execution_flags):
        raise RuntimeError("AfriTPPS execution pillar violation detected")


__all__ = [
    "AFRITPPS_COMPONENT",
    "AFRITPPS_COMPONENT_ID",
    "AFRITPPS_PILLAR",
    "AFRITPPS_STATUS",
    "AFRITPPS_VERSION",
    "QUESTION_ANSWERED",
    "PURPOSE",
    "CAPABILITY_TYPES",
    "MATURITY_LEVELS",
    "WORKFLOW_STEP_STATUSES",
    "EXECUTION_METRIC_TYPES",
    "OUTPUTS",
    "constitutional_afritpps_metadata",
    "assert_afritpps_constitution",
]
