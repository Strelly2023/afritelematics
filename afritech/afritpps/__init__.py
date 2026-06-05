"""AfriTPPS execution pillar.

AfriTPPS defines how work gets executed across capabilities, workflows,
processes, programs, operational models, and execution metrics.
"""

from afritech.afritpps.constants import assert_afritpps_constitution
from afritech.afritpps.models import (
    AfriTPPSCapability,
    AfriTPPSProgram,
    AfriTPPSWorkflow,
    AfriTPPSWorkflowStep,
)
from afritech.afritpps.execution_engine import (
    AfriTPPSExecutionOutcome,
    AfriTPPSOperationIntent,
    execute_operation,
)
from afritech.afritpps.domain_contracts import (
    DOMAIN_CONTRACTS,
    AfriTPPSContractError,
    DomainExecutionContract,
    DomainOperationContract,
    execute_domain_operation,
    get_domain_contract,
)
from afritech.afritpps.orchestration import (
    AfriTPPSOrchestrationIntent,
    AfriTPPSOrchestrationOutcome,
    AfriTPPSOrchestrationError,
    OrchestrationStep,
    execute_orchestration,
)
from afritech.afritpps.observability import (
    DependencyEdge,
    OrchestrationView,
    StepView,
    build_orchestration_view,
    list_orchestration_views,
)
from afritech.afritpps.persistent import (
    OperatorControlError,
    abort_orchestration,
    create_persistent_orchestration,
    execute_persistent_orchestration,
    pause_orchestration,
    resume_orchestration,
)

__all__ = [
    "AfriTPPSCapability",
    "AfriTPPSProgram",
    "AfriTPPSWorkflow",
    "AfriTPPSWorkflowStep",
    "AfriTPPSExecutionOutcome",
    "AfriTPPSOperationIntent",
    "AfriTPPSContractError",
    "DOMAIN_CONTRACTS",
    "DomainExecutionContract",
    "DomainOperationContract",
    "AfriTPPSOrchestrationError",
    "AfriTPPSOrchestrationIntent",
    "AfriTPPSOrchestrationOutcome",
    "OrchestrationStep",
    "DependencyEdge",
    "OrchestrationView",
    "StepView",
    "OperatorControlError",
    "assert_afritpps_constitution",
    "abort_orchestration",
    "build_orchestration_view",
    "create_persistent_orchestration",
    "execute_domain_operation",
    "execute_orchestration",
    "execute_operation",
    "execute_persistent_orchestration",
    "get_domain_contract",
    "list_orchestration_views",
    "pause_orchestration",
    "resume_orchestration",
]
