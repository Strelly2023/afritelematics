from __future__ import annotations

from typing import Callable, Any, Dict

from afritech.runtime.runtime_engine import RuntimeEngine
from afritech.runtime.kernel.execute import ExecutionContext
from afritech.distributed.crypto import NodeIdentity
from afritech.distributed.proof import build_proof
from afritech.epoch.epoch_snapshot import EpochSnapshot


class ZeroTrustNode:
    """
    Zero-Trust Sovereign Node.

    Responsibilities:
    - Execute functions via RuntimeEngine
    - Sign execution results
    - Produce verifiable cryptographic proofs
    - Never trust → always verify
    """

    def __init__(self, node_id: str) -> None:
        if not isinstance(node_id, str):
            raise TypeError("node_id must be a string")

        self.node_id: str = node_id
        self.engine: RuntimeEngine = RuntimeEngine()
        self.identity: NodeIdentity = NodeIdentity()

        # ✅ internal state
        self._last_epoch: int | None = None

    # -----------------------------------------------------
    # Execution (zero-trust proof generation)
    # -----------------------------------------------------

    def execute(
        self,
        fn: Callable[[ExecutionContext], Any],
        epoch_snapshot: EpochSnapshot,
        fn_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Execute and return a signed cryptographic proof.

        Returns:
        {
            "node": str,
            "result": Any,
            "hash": str,
            "signature": str,
            "metadata": optional
        }
        OR
        {
            "node": str,
            "status": "rejected",
            "error": str
        }
        """

        try:
            # ✅ Validate epoch transition
            self._validate_epoch(epoch_snapshot)

            # ✅ Execute under sovereign runtime
            result = self.engine.execute(fn, epoch_snapshot, fn_id=fn_id)

            # ✅ Deterministic signing payload
            payload = self._build_payload(result, epoch_snapshot, fn_id)

            signature = self.identity.sign(payload)

            # ✅ Build proof with metadata
            proof = build_proof(
                node_id=self.node_id,
                result=result,
                signature=signature,
                metadata=payload["metadata"],
            )

            # ✅ Update state
            self._last_epoch = epoch_snapshot.semantic_epoch.number

            return proof

        except Exception as e:
            return {
                "node": self.node_id,
                "status": "rejected",
                "error": str(e),
            }

    # -----------------------------------------------------
    # Payload construction
    # -----------------------------------------------------

    def _build_payload(
        self,
        result: Any,
        epoch_snapshot: EpochSnapshot,
        fn_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Canonical payload used for signing.
        """

        return {
            "node": self.node_id,
            "result": result,
            "metadata": {
                "epoch": epoch_snapshot.semantic_epoch.number,
                "contract_id": fn_id,
            },
        }

    # -----------------------------------------------------
    # Epoch validation
    # -----------------------------------------------------

    def _validate_epoch(self, epoch_snapshot: EpochSnapshot) -> None:
        """
        Ensure valid monotonic epoch transitions.
        """

        if not isinstance(epoch_snapshot, EpochSnapshot):
            raise TypeError("Invalid EpochSnapshot")

        incoming = epoch_snapshot.semantic_epoch.number

        if self._last_epoch is None:
            return

        if incoming < self._last_epoch:
            raise RuntimeError(
                f"Invalid epoch transition: {incoming} < {self._last_epoch}"
            )

    # -----------------------------------------------------
    # Key export (for network distribution)
    # -----------------------------------------------------

    def get_public_key(self) -> bytes:
        """
        Export public key for verification by other nodes.
        """
        return self.identity.serialize_public_key()

    # -----------------------------------------------------
    # State helpers
    # -----------------------------------------------------

    def get_node_id(self) -> str:
        return self.node_id

    def get_current_epoch(self) -> int | None:
        return self._last_epoch

    def reset(self) -> None:
        """
        Reset node state.
        """

        self.engine.reset()
        self._last_epoch = None
