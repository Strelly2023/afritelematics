
#afritech/core/runtime/engine/executor.py
"""
AfriTech Execution Engine
=========================

Deterministic Proof-Carrying Execution Engine.

Constitutional guarantees:

- deterministic execution
- replay-safe output hashing
- immutable execution artifacts
- invariant enforcement
- trace-bound execution topology
- proof-carrying execution semantics
"""

from __future__ import annotations

import asyncio
import json
import traceback

from typing import Any, Callable, Dict, Optional

from afritech.shared.context import (
    RuntimeContext,
)

from afritech.shared.types import (
    ExecutionResult,
)

from afritech.core.runtime.guards.invariant_guard import (
    InvariantGuard,
)

from afritech.core.runtime.guards.proof_validator import (
    ProofValidator,
)

from afritech.proof.proof_artifact import (
    ProofArtifact,
)

from afritech.trace.trace_engine import (
    TraceEngine,
)


# ============================================================
# ERROR
# ============================================================

class ExecutionError(
    Exception
):
    pass


# ============================================================
# EXECUTION ENGINE
# ============================================================

class ExecutionEngine:
    """
    Deterministic constitutional execution engine.
    """

    def __init__(
        self,
        execution_fn: Callable[
            [Dict[str, Any]],
            Dict[str, Any],
        ],
        *,
        trace: Optional[
            TraceEngine
        ] = None,
        event_bus: Optional[
            Any
        ] = None,
        require_proof: bool = True,
        zk_prover: Optional[
            Any
        ] = None,
    ):

        self.execution_fn = (
            execution_fn
        )

        self.trace = trace

        self.event_bus = event_bus

        self.require_proof = (
            require_proof
        )

        self.zk_prover = zk_prover

    # ========================================================
    # MAIN EXECUTION
    # ========================================================

    def execute(
        self,
        context: RuntimeContext,
    ) -> ExecutionResult:

        # ----------------------------------------------------
        # context validation
        # ----------------------------------------------------

        if not isinstance(
            context,
            RuntimeContext,
        ):

            raise ExecutionError(
                "invalid_context_type"
            )

        if not context.verify():

            raise ExecutionError(
                "context_integrity_failed"
            )

        # ----------------------------------------------------
        # pre-invariant enforcement
        # ----------------------------------------------------

        InvariantGuard.enforce_authority(
            context
        )

        InvariantGuard.enforce_closed_world(
            context
        )

        InvariantGuard.enforce_surface(
            context
        )

        InvariantGuard.enforce_no_silent_mutation(
            context
        )

        # ----------------------------------------------------
        # trace initialization
        # ----------------------------------------------------

        if self.trace:

            self.trace.record(

                "execution_start",

                {
                    "context_hash":
                        context.context_hash,
                },
            )

        try:

            # =================================================
            # deterministic execution payload
            # =================================================

            input_payload = {

                "authority_profile":
                    context.authority_profile,

                "payload":
                    context.payload,

                "replay_requirements":
                    context.replay_requirements,
            }

            # =================================================
            # execution
            # =================================================

            output = self.execution_fn(
                input_payload
            )

            if not isinstance(
                output,
                dict,
            ):

                raise ExecutionError(
                    "invalid_output_type"
                )

            # deterministic serialization validation
            json.dumps(

                output,

                sort_keys=True,

                separators=(
                    ",",
                    ":",
                ),

                ensure_ascii=False,
            )

            # =================================================
            # initial immutable result
            # =================================================

            result = ExecutionResult(

                success=True,

                output=output,

                context=context,
            )

            # =================================================
            # invariant enforcement
            # =================================================

            InvariantGuard.enforce_replay_valid(
                result
            )

            if not result.verify():

                raise ExecutionError(
                    "result_hash_mismatch"
                )

            # =================================================
            # proof generation
            # =================================================

            proof = self._generate_proof(

                context=context,

                result=result,
            )

            if self.require_proof:

                ProofValidator.validate(

                    proof,

                    expected_input_hash=
                        proof.input_hash,

                    expected_output_hash=
                        proof.output_hash,
                )

            # =================================================
            # zk proof (optional)
            # =================================================

            zk_proof = None

            if self.zk_prover:

                zk_proof = (
                    self.zk_prover.prove(
                        input_payload,
                        output,
                    )
                )

            # =================================================
            # trace finalization
            # =================================================

            trace_hash = None

            if self.trace:

                self.trace.complete(

                    "execution_start",

                    {
                        "result_hash":
                            result.result_hash,

                        "proof_hash":
                            (
                                proof.proof_hash
                                if proof
                                else None
                            ),
                    },
                )

                trace_hash = (
                    self.trace.finalize()
                )

            # =================================================
            # final immutable result
            # =================================================

            final_result = ExecutionResult(

                success=True,

                output=output,

                context=context,

                proof=proof,

                zk_proof=zk_proof,

                trace_hash=trace_hash,
            )

            if not final_result.verify():

                raise ExecutionError(
                    "final_result_integrity_failed"
                )

            # =================================================
            # success event
            # =================================================

            self._emit({

                "type":
                    "EXECUTION_COMPLETED",

                "context_hash":
                    context.context_hash,

                "result_hash":
                    final_result.result_hash,

                "trace_hash":
                    trace_hash,
            })

            return final_result

        except Exception as exc:

            error_str = (
                self._format_error(exc)
            )

            # ------------------------------------------------
            # finalize trace
            # ------------------------------------------------

            trace_hash = None

            if self.trace:

                self.trace.complete(

                    "execution_start",

                    {
                        "error":
                            error_str,
                    },
                )

                trace_hash = (
                    self.trace.finalize()
                )

            # ------------------------------------------------
            # immutable failure result
            # ------------------------------------------------

            failure_result = ExecutionResult(

                success=False,

                error=error_str,

                context=context,

                trace_hash=trace_hash,
            )

            if not failure_result.verify():

                raise ExecutionError(
                    "failed_result_integrity"
                )

            # ------------------------------------------------
            # failure event
            # ------------------------------------------------

            self._emit({

                "type":
                    "EXECUTION_FAILED",

                "context_hash":
                    context.context_hash,

                "error":
                    error_str,
            })

            return failure_result

    # ========================================================
    # PROOF GENERATION
    # ========================================================

    def _generate_proof(
        self,
        *,
        context: RuntimeContext,
        result: ExecutionResult,
    ) -> ProofArtifact:

        input_data = {

            "authority_profile":
                context.authority_profile,

            "payload":
                context.payload,

            "replay_requirements":
                context.replay_requirements,
        }

        return ProofArtifact(

            theorem=
                "execution_deterministic",

            input_data=
                input_data,

            output_data=
                result.output,

            metadata={

                "context_hash":
                    context.context_hash,

                "result_hash":
                    result.result_hash,
            },
        )

    # ========================================================
    # ERROR FORMATTER
    # ========================================================

    @staticmethod
    def _format_error(
        exc: Exception,
    ) -> str:

        return "".join(

            traceback.format_exception_only(
                type(exc),
                exc,
            )

        ).strip()

    # ========================================================
    # EVENT EMISSION
    # ========================================================

    def _emit(
        self,
        event: Dict[str, Any],
    ) -> None:

        if not self.event_bus:
            return

        try:

            asyncio.create_task(
                self.event_bus.publish(
                    event
                )
            )

        except Exception:

            # event bus failures must not mutate
            # execution semantics
            return