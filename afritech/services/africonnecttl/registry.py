from __future__ import annotations

from typing import Any, Callable, Mapping

from afritech.runtime.kernel.execute import ExecutionContext
from afritech.services.africonnecttl.execution import (
    AFRICONNECTTL_FN_IDS,
    build_operation,
)
from afritech.services.africonnecttl.reducers import shipment_reducer


SURFACE_DEFINITION = {
    "surface": "africonnecttl",
    "domain": "logistics",
    "type": "execution_surface",
    "authority": "replay_only",
    "status": "PLANNED",
    "live_deployment": "FORBIDDEN",
    "truth_source": "replay_receipts_only",
}

SHIPMENT_LIFECYCLE = (
    ("shipment_request", "REQUESTED"),
    ("shipment_assign", "ASSIGNED"),
    ("shipment_pickup", "PICKED_UP"),
    ("shipment_transit", "IN_TRANSIT"),
    ("shipment_delivered", "DELIVERED"),
)

EVIDENCE_FIELDS = (
    "shipment_id",
    "execution_trace",
    "proof_receipts",
    "ledger_block_hash",
    "replay_verification",
    "device_source",
    "timestamps",
)

STOP_CONDITIONS = (
    "replay_mismatch",
    "missing_transition",
    "wrong_state_ordering",
    "unsigned_proof",
    "inconsistent_ledger",
)

STATE_REDUCERS = {
    "africonnecttl.shipment": shipment_reducer,
}


def execution_registry(
    payloads: Mapping[str, Mapping[str, Any]],
) -> dict[str, Callable[[ExecutionContext], dict[str, Any]]]:
    return {
        fn_id: build_operation(fn_id, payloads[fn_id])
        for fn_id in AFRICONNECTTL_FN_IDS
        if fn_id in payloads
    }


def validate_lifecycle(events: list[Mapping[str, Any]]) -> bool:
    observed = tuple(
        (event.get("contract_id"), event.get("status"))
        for event in events
    )
    if observed != SHIPMENT_LIFECYCLE:
        raise RuntimeError(
            "AfriConnectTL lifecycle must be REQUEST -> ASSIGN -> "
            "PICKUP -> TRANSIT -> DELIVERY"
        )
    return True


def validate_surface_contract() -> bool:
    if tuple(fn_id for fn_id, _ in SHIPMENT_LIFECYCLE) != AFRICONNECTTL_FN_IDS:
        raise RuntimeError("AfriConnectTL fn_id registry mismatch")
    if SURFACE_DEFINITION["status"] != "PLANNED":
        raise RuntimeError("AfriConnectTL must remain PLANNED")
    if SURFACE_DEFINITION["live_deployment"] != "FORBIDDEN":
        raise RuntimeError("AfriConnectTL live deployment must remain forbidden")
    if SURFACE_DEFINITION["truth_source"] != "replay_receipts_only":
        raise RuntimeError("AfriConnectTL truth source must remain replay receipts")
    if "africonnecttl.shipment" not in STATE_REDUCERS:
        raise RuntimeError("AfriConnectTL shipment reducer is not registered")
    return True
