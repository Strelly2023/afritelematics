# afritech/runtime/engine/executor.py

"""
AfriTech Execution Engine

Deterministic + Proof‑Carrying Execution Engine

Responsibilities:
- Execute core logic
- Enforce invariants
- Produce reproducible results
- Enforce proof‑carrying execution (PCE)
- Integrate ZK proof generation
- Emit TRACE for causal correctness
"""

from __future__ import annotations

from typing import Dict, Any, Callable, Optional
import traceback
import hashlib
import json

from afritech.runtime.context.runtime_context import RuntimeContext
from afritech.runtime.guards.invariant_guard import InvariantGuard
from afritech.runtime.guards.proof_validator import ProofValidator
from afritech.proof.proof_artifact import ProofArtifact

from afritech.trace.trace_engine import TraceEngine

# ✅ ZK integration
from afritech.zk.interface import ZKProof


# -----------------------------------------------------------------
# EXECUTION ERROR
# -----------------------------------------------------------------

class ExecutionError(Exception):
    pass


# -----------------------------------------------------------------
# EXECUTION RESULT
# -----------------------------------------------------------------

class ExecutionResult:
    """
    Deterministic execution result with proof + trace binding
    """

    def __init__(
        self,
        success: bool,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        context: Optional[RuntimeContext] = None,
        proof: Optional[ProofArtifact] = None,
        zk_proof: Optional[ZKProof] = None,
        trace_hash: Optional[str] = None,
    ):
        self.success = success
        self.output = output or {}
        self.error = error
        self.context = context
        self.proof = proof
        self.zk_proof = zk_proof
        self.trace_hash = trace_hash

        self.timestamp = (
            context.timestamp if context else "UNDEFINED_TIMESTAMP"
        )

        self.result_hash = self._compute_hash()

    # -------------------------------------------------------------
    # CANONICAL SERIALIZATION
    # -------------------------------------------------------------

    @staticmethod
    def _canonical_json(data: Dict[str, Any]) -> str:
        return json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
        )

    # -------------------------------------------------------------
    # HASH
    # -------------------------------------------------------------

    def _compute_hash(self) -> str:
        base = {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "trace_hash": self.trace_hash,
        }

        return hashlib.sha256(
            self._canonical_json(base).encode("utf-8")
        ).hexdigest()

    # -------------------------------------------------------------
    # VERIFY
    # -------------------------------------------------------------

    def verify(self) -> bool:
        return self.result_hash == self._compute_hash()

    # -------------------------------------------------------------
    # EXPORT
    # -------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "context": self.context.to_dict() if self.context else None,
            "result_hash": self.result_hash,
            "trace_hash": self.trace_hash,
            "timestamp": self.timestamp,
            "proof": self.proof.to_dict() if self.proof else None,
            "zk_proof": self.zk_proof.to_dict() if self.zk_proof else None,
        }

    def __repr__(self):
        return (
            f"<ExecutionResult success={self.success} "
            f"hash={self.result_hash[:10]}...>"
        )


# -----------------------------------------------------------------
# EXECUTION ENGINE
# -----------------------------------------------------------------

class ExecutionEngine:
    """
    Deterministic Proof‑Carrying Execution Engine with TRACE integration
    """

    def __init__(
        self,
        execution_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
        *,
        trace: Optional[TraceEngine] = None,
        event_bus: Optional[Any] = None,
        require_proof: bool = True,
        zk_prover: Optional[Any] = None,
    ):
        self.execution_fn = execution_fn
        self.trace = trace
        self.event_bus = event_bus
        self.require_proof = require_proof
        self.zk_prover = zk_prover

    # -----------------------------------------------------------------
    # MAIN EXECUTION
    # -----------------------------------------------------------------

    def execute(self, context: RuntimeContext) -> ExecutionResult:

        # ---------------------------------------------------------
        # CONTEXT VALIDATION
        # ---------------------------------------------------------

        if not isinstance(context, RuntimeContext):
            raise ExecutionError("invalid_context_type")

        if not context.verify():
            raise ExecutionError("context_integrity_failed")

        # ---------------------------------------------------------
        # PRE‑INVARIANTS
        # ---------------------------------------------------------

        InvariantGuard.enforce_authority(context)
        InvariantGuard.enforce_closed_world(context)

        if self.trace:
            self.trace.record(
                "execution_start",
                {"context_hash": context.context_hash},
            )

        try:
            # -----------------------------------------------------
            # EXECUTION
            # -----------------------------------------------------

            input_payload = {
                "authority_profile": context.authority_profile,
                "payload": context.payload,
                "replay_requirements": context.replay_requirements,
            }

            output = self.execution_fn(input_payload)

            if not isinstance(output, dict):
                raise ExecutionError("invalid_output_type")

            # ensure deterministic JSON
            json.dumps(output, sort_keys=True, separators=(",", ":"))

            # -----------------------------------------------------
            # RESULT
            # -----------------------------------------------------

            result = ExecutionResult(
                success=True,
                output=output,
                context=context,
            )

            # -----------------------------------------------------
            # POST‑INVARIANTS
            # -----------------------------------------------------

            InvariantGuard.enforce_replay_valid(result)

            if not result.verify():
                raise ExecutionError("result_hash_mismatch")

            # -----------------------------------------------------
            # PROOF‑CARRYING EXECUTION
            # -----------------------------------------------------

            proof = self._generate_proof(context, result)

            if self.require_proof:
                ProofValidator.validate(
                    proof,
                    expected_input_hash=proof.input_hash,
                    expected_output_hash=proof.output_hash,
                )

            result.proof = proof

            # -----------------------------------------------------
            # ZK PROOF (OPTIONAL)
            # -----------------------------------------------------

            if self.zk_prover:
                zk_proof = self.zk_prover.prove(
                    input_payload,
                    output,
                )
                result.zk_proof = zk_proof

            # -----------------------------------------------------
            # TRACE FINALIZATION (EXECUTION SCOPE)
            # -----------------------------------------------------

            trace_hash = None
            if self.trace:
                self.trace.complete(
                    "execution_start",
                    {
                        "result_hash": result.result_hash,
                        "proof_hash": proof.proof_hash if proof else None,
                    },
                )
                trace_hash = self.trace.finalize()

            result.trace_hash = trace_hash

            # -----------------------------------------------------
            # SUCCESS EVENT
            # -----------------------------------------------------

            self._emit({
                "type": "EXECUTION_COMPLETED",
                "context_hash": context.context_hash,
                "result_hash": result.result_hash,
                "trace_hash": trace_hash,
            })

            return result

        except Exception as e:

            error_str = self._format_error(e)

            if self.trace:
                self.trace.complete(
                    "execution_start",
                    {"error": error_str},
                )
                self.trace.finalize()

            result = ExecutionResult(
                success=False,
                error=error_str,
                context=context,
                trace_hash=self.trace.to_dict().get("trace_root_hash")
                if self.trace else None,
            )

            if not result.verify():
                raise ExecutionError("failed_result_integrity")

            self._emit({
                "type": "EXECUTION_FAILED",
                "context_hash": context.context_hash,
                "error": error_str,
            })

            return result

    # -----------------------------------------------------------------
    # PROOF GENERATION
    # -----------------------------------------------------------------

    def _generate_proof(
        self,
        context: RuntimeContext,
        result: ExecutionResult,
    ) -> ProofArtifact:

        input_data = {
            "authority_profile": context.authority_profile,
            "payload": context.payload,
            "replay_requirements": context.replay_requirements,
        }

        return ProofArtifact(
            theorem="execution_deterministic",
            input_data=input_data,
            output_data=result.output,
            metadata={
                "context_hash": context.context_hash,
                "result_hash": result.result_hash,
            },
        )

    # -----------------------------------------------------------------
    # ERROR FORMATTER
    # -----------------------------------------------------------------

    @staticmethod
    def _format_error(e: Exception) -> str:
        return "".join(
            traceback.format_exception_only(type(e), e)
        ).strip()

    # -----------------------------------------------------------------
    # EVENT EMITTER
    # -----------------------------------------------------------------

    def _emit(self, event: Dict[str, Any]) -> None:
        if not self.event_bus:
            return

        try:
            import asyncio
            asyncio.create_task(self.event_bus.publish(event))
        except Exception:
            pass