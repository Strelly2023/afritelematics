from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Dict, Iterable, List, Mapping


State = Dict[str, Any]
Reducer = Callable[[State, Dict[str, Any]], State]


class LedgerStateMachine:
    """
    Derive protocol state from committed execution blocks.

    The ledger remains history. This state machine is a deterministic projection
    over that history, keyed by proof metadata.contract_id.
    """

    def __init__(self) -> None:
        self._reducers: Dict[str, Reducer] = {}

    def register_reducer(self, contract_id: str, reducer: Reducer) -> None:
        if not isinstance(contract_id, str) or not contract_id:
            raise ValueError("contract_id must be non-empty")
        if not callable(reducer):
            raise TypeError("reducer must be callable")
        self._reducers[contract_id] = reducer

    def replay(
        self,
        blocks: Iterable[Mapping[str, Any]],
        initial_state: Mapping[str, Any] | None = None,
    ) -> State:
        state: State = dict(initial_state or {})

        for block in sorted(blocks, key=lambda item: item.get("index", 0)):
            proofs = block.get("proofs", [])
            if not isinstance(proofs, list):
                continue

            for proof in self._canonical_proofs(proofs):
                if not isinstance(proof, dict):
                    continue

                contract_id = self._contract_id(proof)
                reducer = self._reducers.get(contract_id, self._default_reducer)
                state = reducer(deepcopy(state), deepcopy(proof))

        return state

    def _canonical_proofs(self, proofs: List[Any]) -> List[Dict[str, Any]]:
        canonical: Dict[tuple[str, str], Dict[str, Any]] = {}

        for proof in proofs:
            if not isinstance(proof, dict):
                continue

            key = (
                self._contract_id(proof),
                str(proof.get("hash", "")),
            )
            canonical.setdefault(key, proof)

        return list(canonical.values())

    def replay_ledger(
        self,
        ledger,
        initial_state: Mapping[str, Any] | None = None,
    ) -> State:
        if hasattr(ledger, "verify_chain") and not ledger.verify_chain():
            raise ValueError("ledger chain verification failed")

        if hasattr(ledger, "get_blocks"):
            return self.replay(ledger.get_blocks(), initial_state)

        blocks = getattr(ledger, "_blocks", None)
        if blocks is None:
            raise TypeError("ledger must expose get_blocks() or _blocks")

        return self.replay(
            [block.to_dict() if hasattr(block, "to_dict") else block for block in blocks],
            initial_state,
        )

    def _contract_id(self, proof: Dict[str, Any]) -> str:
        metadata = proof.get("metadata", {})
        if isinstance(metadata, dict) and isinstance(metadata.get("contract_id"), str):
            return metadata["contract_id"]
        return "unknown"

    def _default_reducer(self, state: State, proof: Dict[str, Any]) -> State:
        executions = state.setdefault("executions", [])
        executions.append(
            {
                "node": proof.get("node"),
                "contract_id": self._contract_id(proof),
                "result": proof.get("result"),
                "block_index": proof.get("block_index"),
            }
        )
        return state
