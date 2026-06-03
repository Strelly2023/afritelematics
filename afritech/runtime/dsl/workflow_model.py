"""
AfriTech Workflow Model

PURPOSE:
--------
Represents a parsed workflow in canonical form.

Responsibilities:
- store workflow structure
- provide deterministic representation
- support step metadata (future DSL evolution)
- ensure immutability safety

CRITICAL LAW:
-------------
Workflow Model MAY:
- hold workflow data
- expose read-only helpers

Workflow Model may NOT:
- execute logic
- mutate external state
- introduce behavior
"""

from typing import List, Dict, Optional
import copy


# ============================================================
# ✅ STEP MODEL
# ============================================================

class Step:
    """
    Represents a single workflow step.

    Supports:
    - name (required)
    - metadata (optional)
    """

    def __init__(self, name: str, metadata: Optional[Dict] = None):
        if not isinstance(name, str):
            raise TypeError("[DSL ERROR] Step name must be a string")

        self.name = name
        self.metadata = dict(metadata or {})

    # --------------------------------------------------------
    # ✅ SAFE ACCESS
    # --------------------------------------------------------

    def get(self, key, default=None):
        return self.metadata.get(key, default)

    # --------------------------------------------------------
    # ✅ SERIALIZATION
    # --------------------------------------------------------

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "metadata": dict(self.metadata),
        }

    # --------------------------------------------------------
    # ✅ COMPARISON (DETERMINISM)
    # --------------------------------------------------------

    def __eq__(self, other):
        if not isinstance(other, Step):
            return False
        return self.name == other.name and self.metadata == other.metadata

    def __repr__(self):
        return f"Step(name={self.name})"


# ============================================================
# ✅ WORKFLOW MODEL
# ============================================================

class Workflow:
    """
    Canonical workflow representation.

    Guarantees:
    - deterministic structure
    - safe copying
    - future extensibility
    """

    def __init__(
        self,
        workflow_id: str,
        steps: List,
        metadata: Optional[Dict] = None,
    ):
        if not isinstance(workflow_id, str):
            raise TypeError("[DSL ERROR] Workflow id must be a string")

        if not isinstance(steps, list):
            raise TypeError("[DSL ERROR] Steps must be a list")

        self.id = workflow_id
        self.steps: List[Step] = self._normalize_steps(steps)
        self.metadata = dict(metadata or {})

    # ========================================================
    # ✅ STEP NORMALIZATION
    # ========================================================

    def _normalize_steps(self, steps: List) -> List[Step]:
        """
        Convert raw steps to Step objects.

        Supports:
        - ["step1", "step2"]
        - [Step(...)]
        - [{"name": "step1", "metadata": {...}}]
        """

        normalized = []

        for step in steps:
            if isinstance(step, Step):
                normalized.append(step)

            elif isinstance(step, str):
                normalized.append(Step(step))

            elif isinstance(step, dict):
                if "name" not in step:
                    raise ValueError(f"[DSL ERROR] Step missing name: {step}")

                normalized.append(
                    Step(
                        name=step["name"],
                        metadata=step.get("metadata"),
                    )
                )

            else:
                raise TypeError(f"[DSL ERROR] Invalid step type: {step}")

        return normalized

    # ========================================================
    # ✅ ACCESSORS
    # ========================================================

    def get_steps(self) -> List[Step]:
        return list(self.steps)

    def get_step_names(self) -> List[str]:
        return [step.name for step in self.steps]

    def get_metadata(self, key, default=None):
        return self.metadata.get(key, default)

    # ========================================================
    # ✅ COPY (IMMUTABILITY SAFETY)
    # ========================================================

    def copy(self):
        """
        Deep copy of workflow.
        """

        return Workflow(
            workflow_id=self.id,
            steps=[copy.deepcopy(s.to_dict()) for s in self.steps],
            metadata=dict(self.metadata),
        )

    # ========================================================
    # ✅ SERIALIZATION
    # ========================================================

    def to_dict(self) -> Dict:
        return {
            "workflow": {
                "id": self.id,
                "steps": [s.to_dict() for s in self.steps],
                "metadata": dict(self.metadata),
            }
        }

    # ========================================================
    # ✅ SUMMARY
    # ========================================================

    def summary(self) -> Dict:
        return {
            "id": self.id,
            "step_count": len(self.steps),
            "steps": self.get_step_names(),
        }

    # ========================================================
    # ✅ VALIDATION
    # ========================================================

    def validate(self) -> bool:
        if not self.steps:
            raise ValueError("[DSL ERROR] Workflow must have steps")

        for step in self.steps:
            if not isinstance(step, Step):
                raise Exception("[DSL ERROR] Invalid step object")

        return True

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ========================================================

    def validate_determinism(self) -> bool:
        """
        Ensure consistent representation.
        """

        s1 = self.to_dict()
        s2 = self.to_dict()

        if s1 != s2:
            raise Exception("[DSL ERROR] Non-deterministic workflow")

        return True

    # ========================================================
    # ✅ DEBUG
    # ========================================================

    def debug(self) -> Dict:
        return {
            "workflow_id": self.id,
            "steps": [repr(s) for s in self.steps],
            "metadata": self.metadata,
        }

    # ========================================================
    # ✅ COMPARISON
    # ========================================================

    def __eq__(self, other):
        if not isinstance(other, Workflow):
            return False

        return (
            self.id == other.id
            and self.steps == other.steps
            and self.metadata == other.metadata
        )

    def __repr__(self):
        return f"Workflow(id={self.id}, steps={len(self.steps)})"