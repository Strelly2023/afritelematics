from __future__ import annotations

import hashlib
from typing import Iterable, TypeVar

T = TypeVar("T")


def normalize_node_id(node_id: str) -> int:
    if not isinstance(node_id, str) or not node_id:
        raise ValueError("node_id must be non-empty")

    try:
        return int(node_id, 16)
    except ValueError:
        digest = hashlib.sha256(node_id.encode("utf-8")).hexdigest()
        return int(digest, 16)


def xor_distance(left: str, right: str) -> int:
    return normalize_node_id(left) ^ normalize_node_id(right)


def sort_by_distance(target_id: str, items: Iterable[T], key) -> list[T]:
    return sorted(items, key=lambda item: xor_distance(target_id, key(item)))
