# afritech/runtime/main.py

"""
AfriTech Sovereign Entry Point
==============================

Canonical constitutional runtime admission surface.

This module is the FINAL gate.
It must:
- verify sovereignty
- admit runtime
- terminate

It must NOT:
- delegate
- recurse
- re-enter boot
"""

from __future__ import annotations

from afritech.verify.engine import verify_replay
from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import (
    SemanticEpoch,
    EpochType,
)
from afritech.guards.engine import verify_sovereignty


# ---------------------------------------------------------------------
# Constitutional halt
# ---------------------------------------------------------------------

def constitutional_halt(message: str) -> None:
    raise SystemExit(
        f"\n❌ CONSTITUTIONAL HALT\n{message}\n"
    )


# ---------------------------------------------------------------------
# Epoch reconstruction (AUTHORITATIVE)
# ---------------------------------------------------------------------

def _derive_epoch_snapshot(replay_result) -> EpochSnapshot:
    """
    Materialize authoritative epoch state from replay witness.
    """

    terminal = replay_result.terminal_epoch

    if terminal is None:
        constitutional_halt(
            "Replay produced no terminal epoch"
        )

    if not isinstance(terminal, int):
        constitutional_halt(
            "Replay terminal epoch must be int"
        )

    semantic_epoch = SemanticEpoch(
        number=terminal,
        parent=None if terminal == 0 else terminal - 1,
        epoch_type=(
            EpochType.GENESIS
            if terminal == 0
            else EpochType.EVOLUTION
        ),
        reseal_required=False,
    )

    return EpochSnapshot.from_replay(
        epoch_number=terminal,
        semantic_epoch=semantic_epoch,
        epoch_hash=f"epoch-{terminal}",
    )


# ---------------------------------------------------------------------
# Sovereign runtime boot (TERMINAL)
# ---------------------------------------------------------------------

def main() -> None:
    print(
        "🏛️ AFRITECH SOVEREIGN RUNTIME "
        "BOOT SEQUENCE STARTING"
    )

    print(
        "🔐 Verifying constitutional "
        "lineage..."
    )

    # ---------------------------------------------------------
    # 1. Replay = history oracle
    # ---------------------------------------------------------

    replay_result = verify_replay()

    if not replay_result.valid:
        constitutional_halt(
            "Constitutional replay invalid"
        )

    print("✅ Historical lineage preserved")

    # ---------------------------------------------------------
    # 2. Derive epoch snapshot
    # ---------------------------------------------------------

    epoch_snapshot = _derive_epoch_snapshot(
        replay_result
    )

    print(
        f"🕒 Terminal epoch: "
        f"{epoch_snapshot.number}"
    )

    # ---------------------------------------------------------
    # 3. Sovereignty verification (FINAL)
    # ---------------------------------------------------------

    verify_sovereignty(epoch_snapshot)

    print("✅ Runtime sovereignty verified")

    # ---------------------------------------------------------
    # ✅ TERMINATE SUCCESSFULLY
    # ---------------------------------------------------------

    print("✅ AFRITECH RUNTIME LEGITIMIZED")


# ---------------------------------------------------------------------
# Module execution
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()