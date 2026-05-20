from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Sequence


JSONScalar = str | int | float | bool | None
JSONValue = JSONScalar | Sequence["JSONValue"] | Mapping[str, "JSONValue"]


@dataclass(frozen=True)
class ConcurrentMutation:
    mutation_id: str
    object_id: str
    logical_timestamp: int
    node_id: str
    payload: Mapping[str, JSONValue]

    @property
    def canonical_hash(self) -> str:
        encoded = json.dumps(
            {
                "mutation_id": self.mutation_id,
                "object_id": self.object_id,
                "payload": self.payload,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()


def conflict_sort_key(
    mutation: ConcurrentMutation,
) -> tuple[str, int, str, str]:
    return (
        mutation.canonical_hash,
        mutation.logical_timestamp,
        mutation.node_id,
        mutation.mutation_id,
    )


def resolve_conflicts(
    mutations: Sequence[ConcurrentMutation],
) -> tuple[ConcurrentMutation, ...]:
    return tuple(sorted(mutations, key=conflict_sort_key))
