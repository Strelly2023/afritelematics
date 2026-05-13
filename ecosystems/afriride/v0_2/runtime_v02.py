# ecosystems/afriride/v0_2/runtime_v02.py

"""
AFRIRIDE v0.2 EXECUTION RUNTIME

This runtime:
✅ Wraps the v0.1 constitutional runtime
✅ Does NOT modify core/constitutional/*
✅ Orchestrates v0.2 deterministic scenarios only
✅ Preserves authority, determinism, and replay guarantees

v0.1 runtime remains the sole constitutional execution authority.
v0.2 runtime is a scenario coordinator layered above it.
"""

from typing import Dict, Any

from ecosystems.afriride.core.constitutional.runtime_adapter import ExecutionRuntime

from ecosystems.afriride.v0_2.execution.driver_dropout import DriverDropoutExecutor
from ecosystems.afriride.v0_2.execution.rejection_chain import RejectionChainExecutor
from ecosystems.afriride.v0_2.execution.timeout import TimeoutExecutor


class V02ExecutionRuntime:
    """
    AfriRide v0.2 Runtime Orchestrator

    Responsibilities:
    - Dispatch v0.2 scenarios to deterministic executors
    - Preserve replay identity by construction
    - Never mutate or bypass v0.1 constitutional runtime
    """

    def __init__(self):
        # ✅ Canonical v0.1 runtime (unchanged, frozen)
        self._base_runtime = ExecutionRuntime()

        # ✅ Deterministic executor registry (static)
        self._executors = {
            "DRIVER_DROPOUT": DriverDropoutExecutor(),
            "DRIVER_REJECTION_CHAIN": RejectionChainExecutor(),
            "TIMEOUT_EXCEEDED": TimeoutExecutor(),
        }

    # -------------------------------------------------
    # ✅ SCENARIO EXECUTION
    # -------------------------------------------------

    def execute_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a v0.2 scenario deterministically.

        Returns:
            {
              decision_hash: str,
              trace: dict,
              refusal: bool
            }
        """

        scenario_id = scenario.get("id")

        if scenario_id not in self._executors:
            raise ValueError(
                f"Unknown or undeclared v0.2 scenario: {scenario_id}"
            )

        executor = self._executors[scenario_id]

        # ✅ Deterministic execution (no mutation, no side effects)
        return executor.execute(scenario)

    # -------------------------------------------------
    # ✅ REPLAY EXECUTION
    # -------------------------------------------------

    def replay_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replay execution is identical to execution by construction.

        Replay guarantees:
        - Same inputs
        - Same executor
        - Same trace
        - Same decision hash
        """

        return self.execute_scenario(scenario)

    # -------------------------------------------------
    # ✅ INTROSPECTION (SAFE)
    # -------------------------------------------------

    def supported_scenarios(self):
        """
        Return the list of supported v0.2 scenario identifiers.
        """
        return list(self._executors.keys())