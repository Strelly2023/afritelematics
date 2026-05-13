# ecosystems/afriride/core/constitutional/runtime_adapter.py

"""
AFRIRIDE RUNTIME ADAPTER

This module DOES NOT own execution authority.

It:
- enforces admission (authority + structure)
- enforces guards (invariants + determinism)
- executes domain handlers
- builds deterministic decision traces
- produces cryptographic proofs

Execution authority resides exclusively in:
    afritech/runtime/main.py

This module is:
- deterministic
- replay-safe
- side-effect controlled

Any bypass of this adapter violates system invariants.
"""

import uuid
from typing import Any, Callable, Dict, List

# ✅ Typed Context
from ecosystems.afriride.core.domain.ride_context import (
    AfriRideExecutionContext
)

# ✅ Constitutional Layers
from ecosystems.afriride.core.constitutional.ride_admission import (
    RideAdmissionChecker
)

from ecosystems.afriride.core.constitutional.ride_guards import (
    ALL_GUARDS
)

# ✅ Decision Trace
from ecosystems.afriride.core.constitutional.decision_trace import (
    build_decision_trace,
    hash_trace,
)


# =========================================================
# ✅ GUARD ENGINE
# =========================================================

class RuntimeGuardEngine:
    """
    Executes all guards in strict deterministic order.
    """

    def __init__(self, guards: List):
        self.guards = list(guards)

    def evaluate(self, command: Any, context: AfriRideExecutionContext) -> List[Dict]:
        trace: List[Dict] = []

        for guard in self.guards:
            decision = guard.check(command, context)

            record = {
                "guard": guard.__class__.__name__,
                "allowed": bool(decision.allowed),
                "reason": str(decision.reason),
            }

            trace.append(record)

            if not decision.allowed:
                raise Exception(
                    f"{record['guard']} rejected: {record['reason']}"
                )

        return trace


# =========================================================
# ✅ EXECUTION RUNTIME
# =========================================================

class ExecutionRuntime:
    """
    Full deterministic execution pipeline:

    1. Context validation
    2. Admission (authority + structure)
    3. Guard enforcement (invariants + determinism)
    4. Handler execution (domain logic)
    5. Decision trace generation
    6. Cryptographic proof (SHA256)
    """

    def __init__(self, guards: List = None):
        self.guard_engine = RuntimeGuardEngine(
            guards or ALL_GUARDS
        )

    # -----------------------------------------------------
    # ✅ MAIN EXECUTION PATH
    # -----------------------------------------------------

    def execute(
        self,
        command: Any,
        handler: Callable,
        context: Any
    ) -> Dict:
        """
        Executes command and returns result + proof.

        Output:
        {
            "trace_id": str,
            "result": dict,
            "proof": {
                "trace": dict,
                "hash": str
            }
        }
        """

        trace_id = self._generate_trace_id()

        # -------------------------------------------------
        # ✅ 0. CONTEXT VALIDATION (STRICT)
        # -------------------------------------------------
        if not isinstance(context, AfriRideExecutionContext):
            raise TypeError(
                "ExecutionRuntime requires AfriRideExecutionContext"
            )

        # -------------------------------------------------
        # ✅ 1. ADMISSION
        # -------------------------------------------------
        admission = RideAdmissionChecker.check(command, context)

        if not admission.allowed:
            return self._build_refusal(
                trace_id,
                command,
                context,
                reason=admission.reason,
                stage="admission"
            )

        # -------------------------------------------------
        # ✅ 2. GUARDS
        # -------------------------------------------------
        try:
            guard_trace = self.guard_engine.evaluate(command, context)
        except Exception as e:
            return self._build_refusal(
                trace_id,
                command,
                context,
                reason=str(e),
                stage="guard"
            )

        # -------------------------------------------------
        # ✅ 3. STATE BEFORE
        # -------------------------------------------------
        before = context.state

        # -------------------------------------------------
        # ✅ 4. HANDLER EXECUTION
        # -------------------------------------------------
        result = handler(command)

        self._validate_handler_output(result)

        after = result.get("state")
        events = result.get("events", [])

        # -------------------------------------------------
        # ✅ 5. TRACE
        # -------------------------------------------------
        trace = build_decision_trace(
            trace_id=trace_id,
            command=command,
            guards=guard_trace,
            before=before,
            after=after,
            events=events
        )

        trace_hash = hash_trace(trace)

        # -------------------------------------------------
        # ✅ 6. RETURN SUCCESS
        # -------------------------------------------------
        return {
            "trace_id": trace_id,
            "result": result,
            "proof": {
                "trace": trace,
                "hash": trace_hash,
            }
        }

    # =====================================================
    # ✅ REFUSAL HANDLING (IMPORTANT UPGRADE)
    # =====================================================

    def _build_refusal(
        self,
        trace_id: str,
        command: Any,
        context: AfriRideExecutionContext,
        reason: str,
        stage: str
    ) -> Dict:
        """
        Builds deterministic refusal trace.

        Ensures even failures are:
        - traceable
        - hashable
        - replay-safe
        """

        trace = build_decision_trace(
            trace_id=trace_id,
            command=command,
            guards=[{
                "stage": stage,
                "allowed": False,
                "reason": reason
            }],
            before=context.state,
            after=context.state,
            events=[]
        )

        trace_hash = hash_trace(trace)

        return {
            "trace_id": trace_id,
            "result": {
                "error": reason,
                "stage": stage
            },
            "proof": {
                "trace": trace,
                "hash": trace_hash
            }
        }

    # =====================================================
    # ✅ INTERNAL UTILITIES
    # =====================================================

    def _generate_trace_id(self) -> str:
        return str(uuid.uuid4())

    def _validate_handler_output(self, result: Dict):
        if not isinstance(result, dict):
            raise Exception("Handler must return a dictionary")

        if "state" not in result:
            raise Exception("Handler output missing 'state'")

        if "events" not in result:
            raise Exception("Handler output missing 'events'")

        if not isinstance(result["events"], list):
            raise Exception("'events' must be a list")