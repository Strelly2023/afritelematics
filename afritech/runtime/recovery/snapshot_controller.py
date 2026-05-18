from dataclasses import dataclass
from typing import Any

from afritech.shared.types import stable_hash


@dataclass(frozen=True)
class Snapshot:
    state: dict[str, Any]
    state_hash: str


def create_snapshot(state: dict[str, Any]) -> Snapshot:
    copied = dict(state)
    return Snapshot(state=copied, state_hash=stable_hash(copied))


def verify_snapshot(snapshot: Snapshot) -> bool:
    return stable_hash(snapshot.state) == snapshot.state_hash
