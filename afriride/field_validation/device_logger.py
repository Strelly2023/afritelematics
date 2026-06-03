"""Device-style event logging for field validation."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Mapping


@dataclass(frozen=True)
class DeviceLogEntry:
    device_id: str
    role: str
    online: bool
    event: Mapping[str, Any]
    observed_at: str

    @property
    def log_hash(self) -> str:
        return _canonical_hash(self.canonical_dict(include_hash=False))

    def canonical_dict(self, *, include_hash: bool = True) -> dict[str, object]:
        payload = {
            "device_id": self.device_id,
            "event": _canonicalize(self.event),
            "observed_at": self.observed_at,
            "online": self.online,
            "role": self.role,
        }
        if include_hash:
            payload["log_hash"] = self.log_hash
        return payload


class DeviceLogger:
    """Collect event logs from real or simulated devices."""

    def __init__(self, *, device_id: str, role: str) -> None:
        self.device_id = device_id
        self.role = role
        self._entries: list[DeviceLogEntry] = []

    @property
    def entries(self) -> tuple[DeviceLogEntry, ...]:
        return tuple(self._entries)

    def record(
        self,
        event: Mapping[str, Any],
        *,
        online: bool = True,
        observed_at: str,
    ) -> DeviceLogEntry:
        entry = DeviceLogEntry(
            device_id=self.device_id,
            event=event,
            observed_at=observed_at,
            online=online,
            role=self.role,
        )
        self._entries.append(entry)
        return entry


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize(item) for item in value]
    return value


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            _canonicalize(value),
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()

