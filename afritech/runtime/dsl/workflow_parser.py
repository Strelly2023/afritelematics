"""
AfriTech Workflow Parser

PURPOSE:
--------
Parse workflow definitions (JSON/YAML/dict) into internal model.

Responsibilities:
- validate structure
- normalize workflow format
- ensure deterministic structure
- preserve semantics (CRITICAL)
- support extensibility (future DSL features)

CRITICAL LAW:
-------------
Parser MAY:
- validate input
- normalize workflow

Parser may NOT:
- execute logic
- mutate external state
- introduce new semantics
"""

import json
from typing import Dict, Any

from afritech.runtime.dsl.workflow_model import Workflow


# ============================================================
# ✅ CORE PARSER
# ============================================================

class WorkflowParser:
    """
    Parses workflow definitions into Workflow model.
    """

    # --------------------------------------------------------
    # ✅ PUBLIC ENTRYPOINT
    # --------------------------------------------------------
    def parse(self, data: Any) -> Workflow:
        """
        Accepts:
        - dict
        - JSON string
        - (future: YAML string)

        Returns:
            Workflow
        """

        normalized = self._normalize_input(data)
        self._validate_structure(normalized)

        workflow_dict = normalized["workflow"]

        return Workflow(
            workflow_id=workflow_dict["id"],
            steps=self._normalize_steps(workflow_dict["steps"]),
        )

    # ========================================================
    # ✅ INPUT NORMALIZATION
    # ========================================================

    def _normalize_input(self, data: Any) -> Dict:
        """
        Normalize input into dictionary.
        """

        if isinstance(data, dict):
            return dict(data)

        if isinstance(data, str):
            try:
                return json.loads(data)
            except Exception:
                raise ValueError("[DSL ERROR] Invalid JSON string")

        raise TypeError("[DSL ERROR] Unsupported input type")

    # ========================================================
    # ✅ STRUCTURE VALIDATION
    # ========================================================

    def _validate_structure(self, data: Dict):
        """
        Validate top-level workflow structure.
        """

        if "workflow" not in data:
            raise ValueError("[DSL ERROR] Missing 'workflow' key")

        wf = data["workflow"]

        if not isinstance(wf, dict):
            raise TypeError("[DSL ERROR] 'workflow' must be a dictionary")

        if "id" not in wf:
            raise ValueError("[DSL ERROR] Missing workflow id")

        if "steps" not in wf:
            raise ValueError("[DSL ERROR] Missing workflow steps")

        if not isinstance(wf["steps"], list):
            raise TypeError("[DSL ERROR] 'steps' must be a list")

    # ========================================================
    # ✅ STEP NORMALIZATION (FIXED ✅)
    # ========================================================

    def _normalize_steps(self, steps: list) -> list:
        """
        Normalize steps into canonical format.

        ✅ Preserves metadata (CRITICAL)
        ✅ Converts to WorkflowModel-compatible format

        Supports:
        - ["step1", "step2"]
        - [{"name": "step1"}]
        - [{"name": "step1", "metadata": {...}}]
        """

        normalized = []

        for step in steps:
            # ✅ simple string
            if isinstance(step, str):
                normalized.append({
                    "name": step,
                    "metadata": {}
                })

            # ✅ dict (advanced form)
            elif isinstance(step, dict):
                if "name" not in step:
                    raise ValueError(f"[DSL ERROR] Step missing 'name': {step}")

                if not isinstance(step["name"], str):
                    raise TypeError(f"[DSL ERROR] Step name must be string: {step}")

                metadata = step.get("metadata", {})

                if metadata is not None and not isinstance(metadata, dict):
                    raise TypeError(
                        f"[DSL ERROR] Step metadata must be dict: {step}"
                    )

                normalized.append({
                    "name": step["name"],
                    "metadata": dict(metadata or {}),
                })

            else:
                raise TypeError(f"[DSL ERROR] Invalid step type: {step}")

        return normalized

    # ========================================================
    # ✅ ADVANCED FEATURE HOOKS
    # ========================================================

    def parse_with_metadata(self, data: Any) -> Dict:
        """
        Extended parser version that returns metadata.
        """

        wf = self.parse(data)

        return {
            "workflow": wf,
            "step_count": len(wf.steps),
            "id": wf.id,
        }

    # ========================================================
    # ✅ VALIDATION ONLY (NO OBJECT CREATION)
    # ========================================================

    def validate_only(self, data: Any) -> bool:
        """
        Lightweight validation mode (no Workflow creation).
        """

        normalized = self._normalize_input(data)
        self._validate_structure(normalized)
        self._normalize_steps(normalized["workflow"]["steps"])

        return True

    # ========================================================
    # ✅ SAFE SERIALIZATION
    # ========================================================

    def to_dict(self, workflow: Workflow) -> Dict:
        """
        Convert Workflow model back to dict.
        """

        return {
            "workflow": {
                "id": workflow.id,
                "steps": [
                    {
                        "name": step.name,
                        "metadata": dict(step.metadata),
                    }
                    for step in workflow.steps
                ],
            }
        }