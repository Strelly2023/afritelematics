"""AfriTPPS GA Elite execution services."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from afritech.afritpps.constants import (
    AFRITPPS_COMPONENT,
    AFRITPPS_PILLAR,
    AFRITPPS_STATUS,
    OUTPUTS,
    QUESTION_ANSWERED,
    constitutional_afritpps_metadata,
)
from afritech.afritpps.metrics import build_program_metric_bundle
from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
)
from afritech.afritpps.execution_engine import (
    AfriTPPSExecutionOutcome,
    AfriTPPSOperationIntent,
    execute_operation,
)
from afritech.afritpps.domain_contracts import (
    DOMAIN_CONTRACTS,
    execute_domain_operation,
    get_domain_contract,
)
from afritech.afritpps.orchestration import (
    AfriTPPSOrchestrationIntent,
    AfriTPPSOrchestrationOutcome,
    OrchestrationStep,
    execute_orchestration,
)
from afritech.afritpps.observability import (
    build_orchestration_view,
    list_orchestration_views,
)
from afritech.afritpps.persistent import (
    abort_orchestration,
    create_persistent_orchestration,
    execute_persistent_orchestration,
    pause_orchestration,
    resume_orchestration,
)


def build_program_from_mappings(
    program_id: str,
    name: str,
    capabilities: Iterable[Mapping[str, object]],
    workflows: Iterable[Mapping[str, object]],
) -> AfriTPPSProgram:
    return AfriTPPSProgram(
        program_id=program_id,
        name=name,
        capabilities=tuple(
            AfriTPPSCapability.from_mapping(payload) for payload in capabilities
        ),
        workflows=tuple(AfriTPPSWorkflow.from_mapping(payload) for payload in workflows),
    )


def build_operational_model(program: AfriTPPSProgram) -> dict[str, object]:
    metrics = build_program_metric_bundle(program)

    return {
        "component": AFRITPPS_COMPONENT,
        "pillar": AFRITPPS_PILLAR,
        "status": AFRITPPS_STATUS,
        "question_answered": QUESTION_ANSWERED,
        "outputs": OUTPUTS,
        "constitution": constitutional_afritpps_metadata(),
        "program": program.canonical_dict(),
        "execution_metrics": metrics.canonical_dict(),
        "defines_execution": True,
        "creates_governance_authority": False,
        "creates_proof_authority": False,
        "creates_replay_authority": False,
        "mutates_proof": False,
    }


__all__ = [
    "build_program_from_mappings",
    "build_operational_model",
    "AfriTPPSExecutionOutcome",
    "AfriTPPSOperationIntent",
    "DOMAIN_CONTRACTS",
    "AfriTPPSOrchestrationIntent",
    "AfriTPPSOrchestrationOutcome",
    "OrchestrationStep",
    "execute_domain_operation",
    "execute_orchestration",
    "execute_operation",
    "execute_persistent_orchestration",
    "get_domain_contract",
    "build_orchestration_view",
    "create_persistent_orchestration",
    "list_orchestration_views",
    "pause_orchestration",
    "resume_orchestration",
    "abort_orchestration",
]
