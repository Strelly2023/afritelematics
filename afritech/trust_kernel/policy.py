from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from afritech.trust_kernel.signatures import verify_command_signature


HIGH_VALUE_EVENT_WITNESS_REQUIREMENTS = {
    "TripCompleted": 2,
    "PaymentCaptured": 3,
}


@dataclass(frozen=True)
class Command:
    event_type: str
    actor_id: str
    subject_id: str
    payload: dict[str, Any]
    signature: dict[str, Any]
    witnesses: tuple[dict[str, Any], ...] = ()


def guard_event_integrity(command: Command) -> None:
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
    if not command.signature.get("signature_mode"):
        raise ValueError("signature.signature_mode is required")
    verify_command_signature(
        event_type=command.event_type,
        actor_id=command.actor_id,
        subject_id=command.subject_id,
        payload=command.payload,
        signature=command.signature,
    )

    required = HIGH_VALUE_EVENT_WITNESS_REQUIREMENTS.get(command.event_type, 0)
    if len(command.witnesses) < required:
        raise ValueError(
            f"{command.event_type} requires at least {required} witnesses"
        )
    for witness in command.witnesses:
        if not witness.get("verifier_node"):
            raise ValueError("witness.verifier_node is required")
        if not witness.get("signature"):
            raise ValueError("witness.signature is required")
