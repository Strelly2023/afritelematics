from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from afritech.security.ed25519 import verify_canonical_json


@dataclass(frozen=True)
class DeviceIdentity:
    device_id: str
    user_id: str
    public_key: str
    registered_at: int

    def canonical(self) -> dict[str, Any]:
        return asdict(self)


class DeviceRegistry:
    """In-memory deterministic registry for pilot device identities."""

    def __init__(self) -> None:
        self.devices: dict[str, DeviceIdentity] = {}

    def register(self, identity: DeviceIdentity) -> None:
        if not identity.device_id:
            raise ValueError("device_id must be non-empty")
        if not identity.user_id:
            raise ValueError("user_id must be non-empty")
        if identity.device_id in self.devices:
            raise ValueError("device already registered")
        self.devices[identity.device_id] = identity

    def public_key_for(self, device_id: str) -> str:
        identity = self.devices.get(device_id)
        if identity is None:
            raise ValueError("unregistered device")
        return identity.public_key


class PublicKeyAuthenticator:
    """Verify mobile event signatures using registered device public keys."""

    def __init__(self, registry: DeviceRegistry) -> None:
        self.registry = registry

    def verify(self, event: dict[str, Any], signature: str) -> bool:
        public_key = self.registry.public_key_for(str(event["device_id"]))
        return verify_canonical_json(_signed_payload(event), signature, public_key)


def _signed_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "device_id": event["device_id"],
        "entity_id": event["entity_id"],
        "event_id": event["event_id"],
        "event_type": event["event_type"],
        "logical_clock": event["logical_clock"],
        "payload": event["payload"],
        "timestamp": event["timestamp"],
    }
