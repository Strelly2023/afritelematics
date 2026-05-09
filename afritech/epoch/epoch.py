# afritech/epoch/epoch.py

"""
AfriTech Epoch Model

Purpose:
Define the canonical representation of system time.

Guarantees:
- immutability
- deterministic identity
- structural validity
- replay-safe representation
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any


# -----------------------------------------------------------------
# EPOCH MODEL
# -----------------------------------------------------------------

@dataclass(frozen=True)
class Epoch:
    """
    Canonical immutable epoch.

    Fields:
        id           → logical epoch identifier (string)
        instance_id  → unique instance identifier (prevents reuse)
        version      → monotonic integer (time progression)
        active       → whether epoch is currently active
        sealed       → whether epoch is immutable / finalized
    """

    id: str
    instance_id: str
    version: int
    active: bool
    sealed: bool

    # -------------------------------------------------------------
    # BASIC VALIDATION
    # -------------------------------------------------------------

    def validate(self) -> bool:
        """
        Validate internal consistency of epoch.
        """

        if not isinstance(self.id, str) or not self.id:
            raise ValueError("invalid_epoch_id")

        if not isinstance(self.instance_id, str) or not self.instance_id:
            raise ValueError("invalid_instance_id")

        if not isinstance(self.version, int) or self.version < 0:
            raise ValueError("invalid_epoch_version")

        if not isinstance(self.active, bool):
            raise ValueError("invalid_active_flag")

        if not isinstance(self.sealed, bool):
            raise ValueError("invalid_sealed_flag")

        return True

    # -------------------------------------------------------------
    # STATE CHECKS
    # -------------------------------------------------------------

    def is_active(self) -> bool:
        return self.active

    def is_sealed(self) -> bool:
        return self.sealed

    def is_valid_transition_target(self) -> bool:
        """
        Check if this epoch can be transitioned into.
        """
        return self.active and not self.sealed

    # -------------------------------------------------------------
    # DETERMINISTIC SERIALIZATION
    # -------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Canonical representation (for hashing / registry).
        """

        return {
            "epoch_id": self.id,
            "instance_id": self.instance_id,
            "version": self.version,
            "active": self.active,
            "sealed": self.sealed,
        }

    # -------------------------------------------------------------
    # FACTORY METHOD (SAFE CREATION)
    # -------------------------------------------------------------

    @classmethod
    def create(
        cls,
        id: str,
        instance_id: str,
        version: int,
        active: bool = True,
        sealed: bool = False,
    ) -> "Epoch":
        """
        Safe constructor with validation.
        """

        epoch = cls(
            id=id,
            instance_id=instance_id,
            version=version,
            active=active,
            sealed=sealed,
        )

        epoch.validate()

        return epoch

    # -------------------------------------------------------------
    # EVOLUTION HELPERS
    # -------------------------------------------------------------

    def seal(self) -> "Epoch":
        """
        Return new sealed epoch (immutability enforced).
        """

        if self.sealed:
            return self  # already sealed

        return Epoch(
            id=self.id,
            instance_id=self.instance_id,
            version=self.version,
            active=False,  # sealed = no longer active
            sealed=True,
        )

    def activate(self) -> "Epoch":
        """
        Activate epoch (if allowed).
        """

        if self.sealed:
            raise ValueError("cannot_activate_sealed_epoch")

        return Epoch(
            id=self.id,
            instance_id=self.instance_id,
            version=self.version,
            active=True,
            sealed=False,
        )

    # -------------------------------------------------------------
    # COMPARISON
    # -------------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Epoch):
            return False

        return self.to_dict() == other.to_dict()

    def __lt__(self, other: "Epoch") -> bool:
        """
        Version-based ordering (time progression)
        """

        return self.version < other.version

    # -------------------------------------------------------------
    # DEBUG / LOGGING
    # -------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"<Epoch id={self.id} "
            f"instance={self.instance_id} "
            f"v={self.version} "
            f"active={self.active} "
            f"sealed={self.sealed}>"
        )
