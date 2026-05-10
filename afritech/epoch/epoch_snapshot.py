# afritech/epoch/epoch_snapshot.py

"""
AfriTech Epoch Snapshot
======================

Canonical immutable constitutional epoch carrier.

This file is the exclusive epoch representation permitted
inside constitutional enforcement surfaces.

Constitutional law:

- Epoch meaning originates ONLY from compiled semantic law
- Replay may reconstruct snapshots ONLY via SemanticEpoch
- Raw dicts are forbidden
- Snapshot is immutable
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from afritech.epoch.compiled.semantic_epoch import (
    SemanticEpoch,
    EpochType,
)


# ---------------------------------------------------------------------
# EPOCH SNAPSHOT
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class EpochSnapshot:
    """
    Immutable constitutional epoch fact.

    Binds:

    - semantic epoch authority
    - lineage continuity
    - registry identity hash
    """

    semantic_epoch: SemanticEpoch
    epoch_hash: str

    # -----------------------------------------------------------------
    # STRUCTURAL SANITY
    # -----------------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(
            self.semantic_epoch,
            SemanticEpoch,
        ):
            raise TypeError(
                "semantic_epoch must be SemanticEpoch"
            )

        if (
            not isinstance(self.epoch_hash, str)
            or not self.epoch_hash
        ):
            raise ValueError(
                "epoch_hash must be non-empty string"
            )

        number = self.semantic_epoch.number
        parent = self.semantic_epoch.parent

        if not isinstance(number, int):
            raise TypeError(
                "SemanticEpoch.number must be int"
            )

        if number < 0:
            raise ValueError(
                "Epoch number must be >= 0"
            )

        if number == 0 and parent is not None:
            raise ValueError(
                "Genesis epoch must not declare parent"
            )

        if number > 0 and parent is None:
            raise ValueError(
                "Non-genesis epoch must declare parent"
            )

        if not isinstance(
            self.semantic_epoch.epoch_type,
            EpochType,
        ):
            raise TypeError(
                "epoch_type must be EpochType"
            )

    # -----------------------------------------------------------------
    # CANONICAL ACCESSORS
    # -----------------------------------------------------------------

    @property
    def number(self) -> int:
        return self.semantic_epoch.number

    @property
    def parent(self) -> Optional[int]:
        return self.semantic_epoch.parent

    @property
    def epoch_type(self) -> EpochType:
        return self.semantic_epoch.epoch_type

    @property
    def reseal_required(self) -> bool:
        return self.semantic_epoch.reseal_required

    # -----------------------------------------------------------------
    # REPLAY RECONSTRUCTION
    # -----------------------------------------------------------------

    @classmethod
    def from_replay(
        cls,
        epoch_number: int,
        semantic_epoch: SemanticEpoch,
        epoch_hash: str,
    ) -> "EpochSnapshot":
        """
        Lawful replay reconstruction surface.

        Replay may materialize snapshots ONLY through
        compiled semantic epoch authority.
        """

        if semantic_epoch.number != epoch_number:
            raise ValueError(
                "Replay epoch mismatch"
            )

        return cls(
            semantic_epoch=semantic_epoch,
            epoch_hash=epoch_hash,
        )

    # -----------------------------------------------------------------
    # SERIALIZATION
    # -----------------------------------------------------------------

    def to_dict(self) -> dict:
        """
        Deterministic documentary projection.
        """

        return {
            "number": self.number,
            "parent": self.parent,
            "epoch_type": self.epoch_type.name,
            "reseal_required": self.reseal_required,
            "epoch_hash": self.epoch_hash,
        }

    # -----------------------------------------------------------------
    # DOCUMENTARY REPRESENTATION
    # -----------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            "EpochSnapshot("
            f"number={self.number}, "
            f"parent={self.parent}, "
            f"epoch_type={self.epoch_type.name}, "
            f"epoch_hash='{self.epoch_hash[:12]}...'"
            ")"
        )