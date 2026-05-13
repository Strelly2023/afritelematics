# ecosystems/afriride/v0_2/execution/base.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from ecosystems.afriride.core.constitutional.decision_trace import (
    build_decision_trace,
    hash_trace,
)


class V02ScenarioExecutor(ABC):
    """
    Base class for all AfriRide v0.2 scenario executors.

    Constitutional guarantees:
    - No executor may perform nondeterministic actions
    - All execution MUST emit a structured decision trace
    - All results MUST be replay-hash stable
    - No executor may bypass trace construction
    """

    @abstractmethod
    def execute(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a scenario deterministically.

        Implementations MUST:
        - operate only on scenario-declared inputs
        - respect the v0.2 determinism envelope
        - construct trace inputs explicitly
        - call finalize() exactly once

        Returns:
            {
              "decision_hash": str,
              "trace": dict,
              "refusal": bool
            }
        """
        raise NotImplementedError(
            "Scenario executor must implement execute()"
        )

    # -------------------------------------------------
    # ✅ TRACE CONSTRUCTION (MANDATORY)
    # -------------------------------------------------

    def build_trace(
        self,
        *,
        trace_id: str,
        scenario_id: str,
        command: str,
        guards: List[str],
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
        events: List[str],
    ) -> Dict[str, Any]:
        """
        Build a canonical decision trace.

        This method enforces:
        - explicit state transitions
        - ordered event sequences
        - deterministic serialization
        """

        return build_decision_trace(
            trace_id=trace_id,
            command={
                "scenario_id": scenario_id,
                "command": command,
            },
            guards=guards,
            before=before_state,
            after=after_state,
            events=events,
        )

    # -------------------------------------------------
    # ✅ FINALIZATION (NON-OVERRIDABLE)
    # -------------------------------------------------

    def finalize(
        self,
        *,
        trace: Dict[str, Any],
        refusal: bool = False,
    ) -> Dict[str, Any]:
        """
        Finalize execution result.

        Guarantees:
        - decision_hash is derived ONLY from trace
        - hash is deterministic
        - refusal flag is explicit
        """

        decision_hash = hash_trace(trace)

        return {
            "decision_hash": decision_hash,
            "trace": trace,
            "refusal": refusal,
        }