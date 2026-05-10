# afritech/main.py

"""
AfriTech Sovereign Entry Point
==============================

Canonical constitutional boot surface.

This is the exclusive lawful execution gateway for AfriTech.

Boot sequence:

    1. Verify deterministic constitutional replay
    2. Recover terminal epoch
    3. Materialize authoritative EpochSnapshot
    4. Verify runtime sovereignty
    5. Emit boot attestation
    6. Delegate execution to runtime

Constitutional guarantees:
- Fail closed
- Replay-first admission
- No speculative runtime authority
- Deferred runtime import
"""

from __future__ import annotations

from afritech.verify.engine import verify_replay

from afritech.epoch.epoch_snapshot import EpochSnapshot
from afritech.epoch.compiled.semantic_epoch import (
    SemanticEpoch,
    EpochType,
)

from afritech.guards.engine import (
    verify_sovereignty,
    ConstitutionalViolation,
)

from afritech.audit.emitter import emit_event


# ---------------------------------------------------------------------
# Constitutional halt
# ---------------------------------------------------------------------

def constitutional_halt(message: str) -> None:
    raise SystemExit(
        f"\n❌ CONSTITUTIONAL HALT\n{message}\n"
    )


# ---------------------------------------------------------------------
# Epoch derivation
# ---------------------------------------------------------------------

def _derive_epoch_snapshot(
    replay_result,
) -> EpochSnapshot:
    """
    Materialize authoritative epoch state from replay.
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
# Sovereign boot
# ---------------------------------------------------------------------

def boot() -> None:
    print("🏛️ AFRITECH SOVEREIGN BOOT SEQUENCE STARTING")
    print("🔐 Verifying constitutional lineage...")

    # ------------------------------------------------------------
    # Replay authority
    # ------------------------------------------------------------

    replay_result = verify_replay()

    if not replay_result.valid:
        constitutional_halt(
            "Constitutional replay invalid"
        )

    print("✅ Historical lineage preserved")

    # ------------------------------------------------------------
    # Epoch authority
    # ------------------------------------------------------------

    epoch_snapshot = _derive_epoch_snapshot(
        replay_result
    )

    print(
        f"🕒 Terminal epoch: "
        f"{epoch_snapshot.number}"
    )

    # ------------------------------------------------------------
    # Sovereignty verification
    # ------------------------------------------------------------

    try:
        verify_sovereignty(epoch_snapshot)

    except ConstitutionalViolation as exc:
        constitutional_halt(str(exc))

    print("✅ Runtime sovereignty verified")
    print("✅ Registry seal verified")

    # ------------------------------------------------------------
    # Deferred runtime admission
    # ------------------------------------------------------------

    try:
        from afritech.runtime.main import (
            main as runtime_main,
        )

    except Exception as exc:
        constitutional_halt(
            "Runtime surface failed admission:\n"
            f"{exc}"
        )

    # ------------------------------------------------------------
    # Boot attestation
    # ------------------------------------------------------------

    emit_event(
        event_type="RUNTIME_BOOT_SUCCESS",
        severity_class="C_DOCUMENTARY",
        epoch=epoch_snapshot.number,
        adr=None,
        description=(
            "Sovereign runtime boot completed "
            "successfully. "
            "All constitutional surfaces verified."
        ),
    )

    # ------------------------------------------------------------
    # Sovereign declaration
    # ------------------------------------------------------------

    print("🏛️ Authority root: /afritech")
    print(f"📜 Epoch: {epoch_snapshot.number}")
    print(
        "🟢 AfriTech RUNNING "
        "(STATE: SOVEREIGN)"
    )

    runtime_main()


# ---------------------------------------------------------------------
# Canonical module surface
# ---------------------------------------------------------------------

def main() -> None:
    boot()


# ---------------------------------------------------------------------
# Module execution
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()