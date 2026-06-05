from __future__ import annotations

from typing import Any, Dict

from afritech.distributed.proof import hash_result


class DeterminismValidator:
    def validate(self, expected_result: Any, replay_result: Any) -> Dict[str, Any]:
        expected_hash = hash_result(expected_result)
        replay_hash = hash_result(replay_result)
        return {
            "deterministic": expected_hash == replay_hash,
            "expected_hash": expected_hash,
            "replay_hash": replay_hash,
            "expected_result": expected_result,
            "replay_result": replay_result,
        }
