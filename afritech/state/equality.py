from __future__ import annotations

import hashlib
import json
from typing import Mapping, Any

from afritech.state.state import State
from afritech.state.types import JSONValue, StateHash

#from afritech.state.equality import _canonicalize
from afritech.state.canonical import canonicalize
# ---------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------

def _canonicalize(value: JSONValue) -> Any:
    """
    Convert JSONValue into a fully deterministic structure:

    - Mapping → sorted dict
    - tuple → tuple (recursively canonicalized)
    - primitives → unchanged
    """

    if isinstance(value, Mapping):
        return {
            k: _canonicalize(value[k])
            for k in sorted(value.keys())
        }

    if isinstance(value, tuple):
        return tuple(_canonicalize(v) for v in value)

    return value


# ---------------------------------------------------------------------
# Deep structural equality
# ---------------------------------------------------------------------

def deep_equal(a: JSONValue, b: JSONValue) -> bool:
    return _canonicalize(a) == _canonicalize(b)


# ---------------------------------------------------------------------
# State canonical projection
# ---------------------------------------------------------------------

def _state_to_dict(state: State) -> dict:
    return {
        "kernel_hash": state.kernel_hash,

        "epoch": {
            "id": state.epoch.id,
            "instance_id": state.epoch.instance_id,
            "active": state.epoch.active,
        },

        "registry": _canonicalize(state.registry.payload),
        "vm": _canonicalize(state.vm.payload),
        "governance": _canonicalize(state.governance.payload),

        "provenance": {
            "parent_hash": state.provenance.parent_hash,
            "transition_id": state.provenance.transition_id,
        },

        "attestation": {
            "state_hash": state.attestation.state_hash,
            "verified": state.attestation.verified,
        },
    }


# ---------------------------------------------------------------------
# Deterministic hashing
# ---------------------------------------------------------------------

def compute_state_hash(state: State) -> str:
    """
    Deterministic hash of State based on canonical JSON encoding.
    """

    canonical_dict = _state_to_dict(state)

    encoded = json.dumps(
        canonical_dict,
        sort_keys=True,
        separators=(",", ":"),
    )

    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------
# Equality for State
# ---------------------------------------------------------------------

def state_equal(a: State, b: State) -> bool:
    return compute_state_hash(a) == compute_state_hash(b)





def compute_state_hash_pre_attestation(state: State) -> StateHash:
    """
    Compute the hash of a State excluding attestation.state_hash and verified.

    This avoids self-referential hashing and yields a well-founded identity.
    """

    state_dict = {
        "kernel_hash": state.kernel_hash,
        "epoch": {
            "id": state.epoch.id,
            "instance_id": state.epoch.instance_id,
            "active": state.epoch.active,
        },
        "registry": _canonicalize(state.registry.payload),
        "vm": _canonicalize(state.vm.payload),
        "governance": _canonicalize(state.governance.payload),
        "provenance": {
            "parent_hash": state.provenance.parent_hash,
            "transition_id": state.provenance.transition_id,
        },
        # 🚫 attestation intentionally excluded
    }

    encoded = json.dumps(
        state_dict,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return StateHash(hashlib.sha256(encoded).hexdigest())