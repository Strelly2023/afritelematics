"""Platform-wide canonical encoding and hashing helpers."""

from __future__ import annotations

import base64
from dataclasses import is_dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from hashlib import sha256
import json
from typing import Any
from uuid import UUID

from afritech.core_platform.hash_domains import HASH_DOMAINS, PROTOCOL_HASH_VERSION


class CanonicalEncoder:
    @staticmethod
    def encode(obj: Any) -> bytes:
        normalized = CanonicalEncoder.normalize(obj)
        return json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

    @staticmethod
    def normalize(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return format(obj, "f")
        if isinstance(obj, datetime):
            return obj.astimezone(timezone.utc).isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("ascii")
        if hasattr(obj, "canonical") and callable(obj.canonical):
            return CanonicalEncoder.normalize(obj.canonical())
        if is_dataclass(obj):
            return CanonicalEncoder.normalize(asdict(obj))
        if isinstance(obj, dict):
            return {
                str(key): CanonicalEncoder.normalize(obj[key])
                for key in sorted(obj.keys(), key=lambda key: str(key))
            }
        if isinstance(obj, list):
            return [CanonicalEncoder.normalize(item) for item in obj]
        if isinstance(obj, tuple):
            return [CanonicalEncoder.normalize(item) for item in obj]
        if isinstance(obj, set):
            normalized = [CanonicalEncoder.normalize(item) for item in obj]
            return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, default=str))
        return obj


def hash_obj(obj: Any, *, domain: str) -> str:
    if domain not in HASH_DOMAINS.values():
        raise ValueError(f"unknown_hash_domain:{domain}")
    payload = [PROTOCOL_HASH_VERSION, domain, CanonicalEncoder.normalize(obj)]
    return sha256(CanonicalEncoder.encode(payload)).hexdigest()


__all__ = ["CanonicalEncoder", "hash_obj"]
