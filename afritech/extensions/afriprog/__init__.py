"""AfriProg proposal-only autonomous engineering extension."""

from afritech.extensions.afriprog.code_executor.executor_preview import (
    PatchPreviewExecutor,
    run_patch_preview,
)
from afritech.extensions.afriprog.command_center.task_dispatcher import (
    TaskDispatcher,
)
from afritech.extensions.afriprog.contracts.engineering_receipt import (
    EngineeringReceipt,
    build_engineering_receipt,
)
from afritech.extensions.afriprog.evidence.evidence_generator import (
    EvidenceGenerator,
)
from afritech.extensions.afriprog.design_generator.design_orchestrator import (
    DesignOrchestrator,
    DesignProposal,
)
from afritech.extensions.afriprog.design_generator.design_reviewer import (
    DesignReview,
    DesignReviewer,
)
from afritech.extensions.afriprog.ai_engine.task_generator import (
    TaskGenerator,
)
from afritech.extensions.afriprog.ai_engine.coder import (
    Coder,
)
from afritech.extensions.afriprog.ai_engine.design_generator import (
    DesignGenerator,
    StructuredDesignOutput,
)
from afritech.extensions.afriprog.ai_engine.design_output_validator import (
    DesignOutputValidationResult,
    DesignOutputValidator,
)
from afritech.extensions.afriprog.ai_engine.objective_engine import (
    Objective,
    ObjectiveEngine,
    ObjectiveEvaluation,
    SuccessCriterion,
)
from afritech.extensions.afriprog.execution.loop_engine import (
    VerificationLoopEngine,
    VerificationLoopResult,
)
from afritech.extensions.afriprog.monitoring.lifecycle_monitor import (
    LifecycleMonitor,
)
from afritech.extensions.afriprog.orchestrator import (
    AfriProgOrchestrator,
    run_phase_2_preview,
)
from afritech.extensions.afriprog.repository_intelligence.orchestrator_preview import (
    run_repository_intelligence,
)

__all__ = [
    "AfriProgOrchestrator",
    "Coder",
    "DesignOrchestrator",
    "DesignProposal",
    "DesignGenerator",
    "DesignOutputValidationResult",
    "DesignOutputValidator",
    "DesignReview",
    "DesignReviewer",
    "EngineeringReceipt",
    "EvidenceGenerator",
    "LifecycleMonitor",
    "Objective",
    "ObjectiveEngine",
    "ObjectiveEvaluation",
    "PatchPreviewExecutor",
    "SuccessCriterion",
    "StructuredDesignOutput",
    "TaskDispatcher",
    "TaskGenerator",
    "VerificationLoopEngine",
    "VerificationLoopResult",
    "build_engineering_receipt",
    "run_patch_preview",
    "run_phase_2_preview",
    "run_repository_intelligence",
]
