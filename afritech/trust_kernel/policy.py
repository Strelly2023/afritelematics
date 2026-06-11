from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from afritech.trust_kernel.signatures import verify_command_signature


# ------------------------------------------------------------------------------------
# WITNESS REQUIREMENTS (HIGH VALUE EVENTS)
# ------------------------------------------------------------------------------------

HIGH_VALUE_EVENT_WITNESS_REQUIREMENTS: Dict[str, int] = {
    "TripCompleted": 2,
    "PaymentCaptured": 3,
}


# ------------------------------------------------------------------------------------
# COMMAND DATA MODEL
# ------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Command:
    """Immutable command representing an intent to mutate system state."""

    event_type: str
    actor_id: str
    subject_id: str
    payload: Dict[str, Any]
    signature: Dict[str, Any]
    witnesses: Tuple[Dict[str, Any], ...] = ()


# ------------------------------------------------------------------------------------
# INTEGRITY GUARD
# ------------------------------------------------------------------------------------

def guard_event_integrity(command: Command) -> None:
    """Validate command integrity before it enters the event pipeline."""

    # --------------------------------------------------------------------------
    # REQUIRED FIELDS
    # --------------------------------------------------------------------------

    if not command.event_type:
        raise ValueError("event_type is required")

    if not command.actor_id:
        raise ValueError("actor_id is required")

    if not command.subject_id:
        raise ValueError("subject_id is required")

    if not isinstance(command.payload, dict):
        raise TypeError("payload must be a dictionary")

    if not isinstance(command.signature, dict):
        raise TypeError("signature must be a dictionary")

    # --------------------------------------------------------------------------
    # SIGNATURE VALIDATION
    # --------------------------------------------------------------------------

    signature_mode = command.signature.get("signature_mode")

    if not signature_mode:
        raise ValueError("signature.signature_mode is required")

    verify_command_signature(
        event_type=command.event_type,
        actor_id=command.actor_id,
        subject_id=command.subject_id,
        payload=command.payload,
        signature=command.signature,
    )

    # --------------------------------------------------------------------------
    # WITNESS ENFORCEMENT
    # --------------------------------------------------------------------------

    required = HIGH_VALUE_EVENT_WITNESS_REQUIREMENTS.get(
        command.event_type,
        0,
    )

    if len(command.witnesses) < required:
        raise ValueError(
            f"{command.event_type} requires at least {required} witnesses"
        )

    # --------------------------------------------------------------------------
    # WITNESS VALIDATION
    # --------------------------------------------------------------------------

    for idx, witness in enumerate(command.witnesses):
        if not isinstance(witness, dict):
            raise TypeError(f"witness[{idx}] must be a dictionary")

        verifier_node = witness.get("verifier_node")
        signature = witness.get("signature")

        if not verifier_node or not isinstance(verifier_node, str):
            raise ValueError("witness.verifier_node is required")

        if not signature or not isinstance(signature, str):
            raise ValueError("witness.signature is required")