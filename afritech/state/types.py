from __future__ import annotations

from dataclasses import dataclass
from typing import NewType, Mapping


# ---------------------------------------------------------------------
# Strong primitive identities
# ---------------------------------------------------------------------

KernelHash = NewType("KernelHash", str)
StateHash = NewType("StateHash", str)

EpochId = NewType("EpochId", str)
EpochInstanceId = NewType("EpochInstanceId", str)

TransitionId = NewType("TransitionId", str)


# ---------------------------------------------------------------------
# Deterministic JSON-like value space
# ---------------------------------------------------------------------
# This defines the admissible universe of state values.
# It excludes:
#   - mutable containers (list, set)
#   - unordered structures
#   - arbitrary objects
#
# This makes deep equality, canonical serialization,
# and deterministic hashing possible later.

JSONPrimitive = str | int | float | bool | None
JSONValue = JSONPrimitive | tuple["JSONValue", ...] | Mapping[str, "JSONValue"]


# ---------------------------------------------------------------------
# Governed projections (opaque at the State boundary)
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RegistryState:
    payload: Mapping[str, JSONValue]


@dataclass(frozen=True)
class VMState:
    payload: Mapping[str, JSONValue]


@dataclass(frozen=True)
class GovernanceState:
    payload: Mapping[str, JSONValue]