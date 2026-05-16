"""
AfriTech Epoch Loaders
=====================

Canonical normalization of epoch representations
into EpochSnapshot.

This module is the ONLY lawful bridge from:
- registry history YAML
- runtime epoch objects
- sealed registry state

into constitutional enforcement logic.

Raw YAML dicts and mutable runtime objects MUST NOT
be consumed directly by constitutional law.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from afritech.registry.loader import load_registry
from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.guards.engine import fail, ViolationClass


# ---------------------------------------------------------------------
# REGISTRY → SNAPSHOT (AUTHORITATIVE)
# ---------------------------------------------------------------------

def load_current_epoch_snapshot() -> EpochSnapshot:
    """
    Load the current sealed epoch snapshot from the registry.

    This is the ONLY function allowed to provide
    epoch authority to runtime sovereignty checks.

    FAIL-CLOSED.
    """

    registry = load_registry()

    # ✅ Correct schema access
    epoch_section = registry.get("epoch")

    if not isinstance(epoch_section, dict):
        fail(
            "missing_epoch_section",
            ViolationClass.A_FATAL,
        )

    if "current" not in epoch_section:
        fail(
            "missing_epoch_current",
            ViolationClass.A_FATAL,
        )

    current_epoch = epoch_section["current"]

    try:
        # ✅ Construct canonical snapshot
        return EpochSnapshot(
            number=current_epoch,
            parent=epoch_section.get("constitutional_epoch"),
            epoch_hash=registry.get("attestation", {}).get("registry_hash"),
        )

    except Exception as e:
        fail(
            f"invalid_epoch_snapshot:{e}",
            ViolationClass.A_FATAL,
        )


# ---------------------------------------------------------------------
# HISTORY → SNAPSHOT
# ---------------------------------------------------------------------

def load_epoch_snapshot_from_history(
    path: str | Path,
) -> EpochSnapshot:
    """
    Load and normalize an epoch snapshot from a registry
    history YAML file (epoch_*.yaml).

    This function performs:
    - strict structural validation
    - no inference
    - no mutation
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Epoch history file not found: {path}")

    data = yaml.safe_load(path.read_text())

    if not isinstance(data, dict):
        raise ValueError("Epoch history file must parse to a dict")

    # Required sections
    if "epoch" not in data:
        raise ValueError("Epoch history missing 'epoch' section")

    if "hash_chain" not in data:
        raise ValueError("Epoch history missing 'hash_chain' section")

    epoch_section = data["epoch"]
    hash_chain = data["hash_chain"]

    if not isinstance(epoch_section, dict):
        raise ValueError("'epoch' section must be a dict")

    if not isinstance(hash_chain, dict):
        raise ValueError("'hash_chain' section must be a dict")

    # Required fields
    if "number" not in epoch_section:
        raise ValueError("Epoch history missing epoch.number")

    if "epoch_hash" not in hash_chain:
        raise ValueError("Epoch history missing hash_chain.epoch_hash")

    number = epoch_section["number"]
    parent = epoch_section.get("parent")
    epoch_hash = hash_chain["epoch_hash"]

    return EpochSnapshot(
        number=number,
        parent=parent,
        epoch_hash=epoch_hash,
    )


# ---------------------------------------------------------------------
# RUNTIME → SNAPSHOT
# ---------------------------------------------------------------------

def load_epoch_snapshot_from_runtime(
    epoch_obj: Any,
) -> EpochSnapshot:
    """
    Normalize a runtime epoch object into EpochSnapshot.

    The runtime epoch object MUST expose:
    - number
    - parent
    - epoch_hash

    No attribute inference is performed.
    """

    try:
        number = epoch_obj.number
        parent = epoch_obj.parent
        epoch_hash = epoch_obj.epoch_hash

    except AttributeError as exc:
        raise ValueError(
            "Runtime epoch object must expose "
            "'number', 'parent', and 'epoch_hash'"
        ) from exc

    return EpochSnapshot(
        number=number,
        parent=parent,
        epoch_hash=epoch_hash,
    )