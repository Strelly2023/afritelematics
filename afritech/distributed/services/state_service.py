from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping

from afritech.distributed.state.state_machine import LedgerStateMachine, Reducer


class StateService:
    """
    Read-only service facade over ledger-derived protocol state.
    """

    def __init__(
        self,
        state_machine: LedgerStateMachine | None = None,
        initial_state: Mapping[str, Any] | None = None,
    ) -> None:
        self.state_machine = state_machine or LedgerStateMachine()
        self._state: Dict[str, Any] = dict(initial_state or {})

    def register_reducer(self, contract_id: str, reducer: Reducer) -> None:
        self.state_machine.register_reducer(contract_id, reducer)

    def refresh_from_ledger(self, ledger) -> Dict[str, Any]:
        self._state = self.state_machine.replay_ledger(ledger, self._state)
        return self.snapshot()

    def load_state(self, state: Mapping[str, Any]) -> None:
        self._state = dict(state)

    def snapshot(self) -> Dict[str, Any]:
        return deepcopy(self._state)

    def get_ride(self, ride_id: str) -> Dict[str, Any] | None:
        return deepcopy(self._state.get("rides", {}).get(ride_id))

    def get_receipt(self, receipt_id: str) -> Dict[str, Any] | None:
        return deepcopy(self._state.get("receipts", {}).get(receipt_id))

    def get_account_balance(self, account_id: str) -> int | float | None:
        return self._state.get("balances", {}).get(account_id)

    def get_shipment(self, shipment_id: str) -> Dict[str, Any] | None:
        return deepcopy(self._state.get("shipments", {}).get(shipment_id))

    def get_lot(self, lot_id: str) -> Dict[str, Any] | None:
        return deepcopy(self._state.get("lots", {}).get(lot_id))

    def list_executions(self) -> list[Dict[str, Any]]:
        return deepcopy(self._state.get("executions", []))
