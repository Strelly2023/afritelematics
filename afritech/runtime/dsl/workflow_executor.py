"""
AfriTech Workflow Executor

PURPOSE:
--------
Executes DSL-defined workflows using the async runtime.

CAPABILITIES:
-------------
- sequential execution
- conditional execution (basic)
- per-step metadata support
- deterministic flow
- non-intrusive (no mutation)

CRITICAL LAW:
-------------
Executor MAY:
- trigger events via dispatcher
- evaluate step conditions
- collect results

Executor may NOT:
- mutate workflow definition
- alter dispatcher semantics
- introduce non-determinism
"""

from typing import Dict, List, Callable, Optional
from afritech.runtime.async_runtime.dispatcher import dispatch_event
from afritech.runtime.dsl.workflow_model import Workflow, Step


# ============================================================
# ✅ STEP REGISTRY
# ============================================================

class StepRegistry:
    """
    Registry mapping step names to callable functions.
    """

    def __init__(self):
        self._steps: Dict[str, Callable] = {}

    def register(self, name: str, func: Callable):
        if not callable(func):
            raise TypeError(f"[DSL ERROR] Step '{name}' must be callable")

        self._steps[name] = func

    def get(self, name: str) -> Callable:
        if name not in self._steps:
            raise Exception(f"[DSL ERROR] Unknown step: {name}")

        return self._steps[name]

    def exists(self, name: str) -> bool:
        return name in self._steps

    def list(self) -> List[str]:
        return list(self._steps.keys())


# ============================================================
# ✅ WORKFLOW EXECUTOR
# ============================================================

class WorkflowExecutor:
    """
    Executes workflows using dispatcher + runtime.

    Supports:
    - sequential flow
    - conditional execution
    - metadata-driven behavior
    """

    def __init__(self, step_registry: StepRegistry):
        self.registry = step_registry

    # ========================================================
    # ✅ MAIN EXECUTION
    # ========================================================

    def execute(self, workflow: Workflow, queue_runtime, context) -> Dict:
        """
        Execute workflow sequentially.
        """

        workflow.validate()

        results = []
        runtime_context = {}

        for step in workflow.steps:
            result = self._execute_step(
                step,
                queue_runtime,
                context,
                runtime_context,
                results,
            )

            if result is None:
                continue

            results.append(result)

        return {
            "workflow_id": workflow.id,
            "steps": results,
        }

    # ========================================================
    # ✅ STEP EXECUTION
    # ========================================================

    def _execute_step(
        self,
        step: Step,
        queue_runtime,
        context,
        runtime_context: dict,
        previous_results: list,
    ) -> Optional[Dict]:
        """
        Execute a single step with optional conditions.
        """

        # ----------------------------------------------------
        # ✅ CONDITION CHECK
        # ----------------------------------------------------
        if not self._should_execute(step, runtime_context):
            return {
                "step": step.name,
                "status": "skipped",
            }

        # ----------------------------------------------------
        # ✅ GET STEP FUNCTION
        # ----------------------------------------------------
        func = self.registry.get(step.name)

        # ----------------------------------------------------
        # ✅ EXECUTE USER LOGIC
        # ----------------------------------------------------
        event = func(context=context, runtime=runtime_context)

        if not isinstance(event, dict):
            raise TypeError(
                f"[DSL ERROR] Step '{step.name}' must return event dict"
            )

        # ----------------------------------------------------
        # ✅ DISPATCH EVENT
        # ----------------------------------------------------
        result = dispatch_event(
            envelope=event,
            queue_runtime=queue_runtime,
            context=context,
        )

        # ----------------------------------------------------
        # ✅ STORE STEP OUTPUT
        # ----------------------------------------------------
        runtime_context[step.name] = result

        return {
            "step": step.name,
            "status": "executed",
            "result": result,
        }

    # ========================================================
    # ✅ CONDITIONAL EXECUTION
    # ========================================================

    def _should_execute(self, step: Step, runtime_context: dict) -> bool:
        """
        Evaluate conditions from metadata.

        Supported metadata:
        {
            "if": "previous_step_name"
        }
        """

        condition = step.metadata.get("if")

        if not condition:
            return True

        # ✅ basic condition: previous step must exist
        return condition in runtime_context

    # ========================================================
    # ✅ SAFE EXECUTION (NO THROW)
    # ========================================================

    def execute_safe(self, workflow: Workflow, queue_runtime, context) -> Dict:
        """
        Execution wrapper that captures step-level failures.
        """

        results = []

        for step in workflow.steps:
            try:
                step_result = self._execute_step(
                    step,
                    queue_runtime,
                    context,
                    {},
                    results,
                )
                results.append(step_result)

            except Exception as e:
                results.append({
                    "step": step.name,
                    "status": "failed",
                    "error": str(e),
                })

                # stop execution on failure
                break

        return {
            "workflow_id": workflow.id,
            "steps": results,
        }

    # ========================================================
    # ✅ DRY RUN (NO DISPATCH)
    # ========================================================

    def preview(self, workflow: Workflow) -> Dict:
        """
        Returns workflow structure without execution.
        """

        return {
            "workflow_id": workflow.id,
            "steps": [step.name for step in workflow.steps],
        }

    # ========================================================
    # ✅ VALIDATION
    # ========================================================

    def validate_registry(self, workflow: Workflow):
        """
        Ensures all steps are registered.
        """

        for step in workflow.steps:
            if not self.registry.exists(step.name):
                raise Exception(f"[DSL ERROR] Step not registered: {step.name}")

        return True