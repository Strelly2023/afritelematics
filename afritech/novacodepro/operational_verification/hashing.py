from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from typing import Any


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def domain_hash(domain: str, payload: dict[str, Any]) -> str:
    material = f"{domain}:{canonical_json(payload)}".encode("utf-8")
    return f"sha256:{hashlib.sha256(material).hexdigest()}"


def without_integrity_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in {"integrity_hash", "signature", "checksum"}}
