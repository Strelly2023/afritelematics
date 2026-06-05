from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def sha256_payload(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def event_hash(
    *,
    event_id: str,
    event_type: str,
    actor_id: str,
    subject_id: str,
    prev_hash: str,
    payload: dict[str, Any],
    signature: dict[str, Any],
) -> str:
    return sha256_payload(
        {
            "event_id": event_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "subject_id": subject_id,
            "prev_hash": prev_hash,
            "payload": payload,
            "signature": signature,
        }
    )
