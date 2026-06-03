"""
AfriTech Workflow Validator

PURPOSE:
--------
Validate DSL workflows before execution.

Responsibilities:
- validate structure
- validate steps
- validate registry compatibility
- enforce deterministic rules
- validate metadata (basic + extensible)

CRITICAL LAW:
-------------
Validator MAY:
- inspect workflows
- raise validation errors

Validator may NOT:
- mutate workflows
- execute logic
- introduce side effects
"""

from typing import Any
from afritech.runtime.dsl.workflow_model import Workflow, Step
from afritech.runtime.dsl.step_registry import StepRegistry


# ============================================================
# ✅ CORE VALIDATOR
# ============================================================

class WorkflowValidator:
    """
    Validates Workflow objects and DSL inputs.
    """

    def __init__(self, step_registry: StepRegistry = None):
        self.registry = step_registry

    # ========================================================
    # ✅ MAIN VALIDATION ENTRY
    # ========================================================

    def validate(self, workflow: Workflow) -> bool:
        """
        Full validation pipeline.
        """

        self._validate_workflow_object(workflow)
        self._validate_steps(workflow)
        self._validate_metadata(workflow)

        if self.registry:
            self._validate_registry(workflow)

        self._validate_determinism(workflow)

        return True

    # ========================================================
    # ✅ STRUCTURE VALIDATION
    # ========================================================

    def _validate_workflow_object(self, workflow: Any):
        if not isinstance(workflow, Workflow):
            raise TypeError("[DSL ERROR] Invalid workflow object")

        if not isinstance(workflow.id, str):
            raise TypeError("[DSL ERROR] Workflow id must be string")

        if not isinstance(workflow.steps, list):
            raise TypeError("[DSL ERROR] Workflow steps must be list")

        if not workflow.steps:
            raise ValueError("[DSL ERROR] Workflow must contain steps")

    # ========================================================
    # ✅ STEP VALIDATION
    # ========================================================

    def _validate_steps(self, workflow: Workflow):
        for i, step in enumerate(workflow.steps):
            if not isinstance(step, Step):
                raise TypeError(f"[DSL ERROR] Invalid step at index {i}")

            if not isinstance(step.name, str):
                raise TypeError(f"[DSL ERROR] Step name must be string: {step}")

            if step.name.strip() == "":
                raise ValueError(f"[DSL ERROR] Step name cannot be empty: {step}")

    # ========================================================
    # ✅ REGISTRY VALIDATION
    # ========================================================

    def _validate_registry(self, workflow: Workflow):
        for step in workflow.steps:
            if not self.registry.exists(step.name):
                raise Exception(f"[DSL ERROR] Step not registered: {step.name}")

    # ========================================================
    # ✅ METADATA VALIDATION
    # ========================================================

    def _validate_metadata(self, workflow: Workflow):
        """
        Validate metadata for future DSL features.
        """

        for step in workflow.steps:
            metadata = step.metadata

            if not isinstance(metadata, dict):
                raise TypeError(
                    f"[DSL ERROR] Metadata must be dict for step: {step.name}"
                )

            # ✅ CONDITIONAL SUPPORT
            condition = metadata.get("if")
            if condition:
                if not isinstance(condition, str):
                    raise TypeError(
                        f"[DSL ERROR] 'if' must be string in step: {step.name}"
                    )

            # ✅ RETRY SUPPORT (future-safe)
            retry = metadata.get("retry")
            if retry is not None:
                if not isinstance(retry, int) or retry < 0:
                    raise ValueError(
                        f"[DSL ERROR] Invalid retry in step: {step.name}"
                    )

            # ✅ TIMEOUT SUPPORT
            timeout = metadata.get("timeout")
            if timeout is not None:
                if not isinstance(timeout, (int, float)) or timeout <= 0:
                    raise ValueError(
                        f"[DSL ERROR] Invalid timeout in step: {step.name}"
                    )

    # ========================================================
    # ✅ DETERMINISM VALIDATION
    # ========================================================

    def _validate_determinism(self, workflow: Workflow):
        """
        Ensure workflow representation is stable.
        """

        d1 = workflow.to_dict()
        d2 = workflow.to_dict()

        if d1 != d2:
            raise Exception("[DSL ERROR] Non-deterministic workflow structure")

    # ========================================================
    # ✅ LIGHT VALIDATION (FAST MODE)
    # ========================================================

    def validate_light(self, workflow: Workflow) -> bool:
        """
        Fast validation without registry checks.
        Useful for high-throughput scenarios.
        """

        self._validate_workflow_object(workflow)
        self._validate_steps(workflow)
        return True

    # ========================================================
    # ✅ VALIDATE SINGLE STEP
    # ========================================================

    def validate_step(self, step: Step) -> bool:
        """
        Validate a single step (useful for incremental workflows).
        """

        if not isinstance(step, Step):
            raise TypeError("[DSL ERROR] Invalid step")

        if not isinstance(step.name, str):
            raise TypeError("[DSL ERROR] Step name must be string")

        if step.name.strip() == "":
            raise ValueError("[DSL ERROR] Step name cannot be empty")

        if self.registry and not self.registry.exists(step.name):
            raise Exception(f"[DSL ERROR] Step not registered: {step.name}")

        return True

    # ========================================================
    # ✅ WORKFLOW COMPATIBILITY CHECK
    # ========================================================

    def validate_compatibility(self, workflow: Workflow, registry: StepRegistry):
        """
        Validate workflow against specific registry snapshot.
        Useful for versioned environments.
        """

        for step in workflow.steps:
            if not registry.exists(step.name):
                raise Exception(
                    f"[DSL ERROR] Step '{step.name}' not compatible with registry"
                )

        return True

    # ========================================================
    # ✅ DEBUG
    # ========================================================

    def debug(self, workflow: Workflow):
        """
        Debug validation report.
        """

        return {
            "workflow_id": workflow.id,
            "step_count": len(workflow.steps),
            "steps": workflow.get_step_names(),
            "valid": True,
        }