from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from afritech.distributed.proof import validate_proof_structure
from afritech.distributed.replay.determinism_validator import DeterminismValidator
from afritech.distributed.replay.reexecutor import ReplayRequest, Reexecutor


class ReplayVerifier:
    def __init__(self, registry: Mapping[str, Callable]) -> None:
        self.reexecutor = Reexecutor(registry)
        self.validator = DeterminismValidator()

    def verify(self, proof: Dict[str, Any], fn_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if not validate_proof_structure(proof):
            return {"replay_verified": False, "reason": "invalid_proof"}

        metadata = proof.get("metadata", {})
        epoch_snapshot = metadata.get("epoch_snapshot")
        if epoch_snapshot is None:
            return {"replay_verified": False, "reason": "missing_epoch_snapshot"}

        request = ReplayRequest(
            fn_id=fn_id,
            args=args,
            epoch_snapshot=epoch_snapshot,
            expected_result=proof["result"],
            expected_hash=proof["hash"],
        )
        replay_result = self.reexecutor.reexecute(request)
        validation = self.validator.validate(proof["result"], replay_result)
        return {
            "replay_verified": validation["deterministic"],
            "proof_hash": proof["hash"],
            **validation,
        }
