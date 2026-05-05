from __future__ import annotations

from pathlib import Path
import yaml
import datetime

from afritech.guards.engine import verify_authority_for_epoch
from afritech.registry.sovereignty import seal_registry
from afritech.audit.emitter import emit_event

# ---------------------------------------------------------------------
# Constitutional failure
# ---------------------------------------------------------------------

def constitutional_halt(msg: str) -> None:
    raise SystemExit(f"\n❌ CONSTITUTIONAL VIOLATION\n{msg}\n")


# ---------------------------------------------------------------------
# Advance epoch
# ---------------------------------------------------------------------

def advance_epoch(adr_id: str) -> None:
    """
    Lawfully advance the constitutional epoch.

    Preconditions (pre‑mutation authority):
    - Registry exists and is SEALED
    - Kernel structural immutability holds
    - Dependency law holds
    - ADR exists

    Effects:
    - Epoch increments by exactly +1
    - Registry is explicitly UNSEALED for mutation
    - Immutable epoch history is recorded
    - Registry is resealed under new identity
    """

    # -----------------------------------------------------------------
    # 1. Verify authority ONLY (no hash enforcement)
    # -----------------------------------------------------------------
    verify_authority_for_epoch()

    base = Path(__file__).resolve().parents[2]
    registry_path = base / "registry" / "registry.yaml"
    history_dir = base / "registry" / "history"

    if not registry_path.exists():
        constitutional_halt("registry.yaml missing")

    with open(registry_path, "r") as f:
        registry = yaml.safe_load(f)

    # -----------------------------------------------------------------
    # 2. Validate ADR existence
    # -----------------------------------------------------------------
    adr_path = base / "governance" / "adr" / f"{adr_id}.md"
    if not adr_path.exists():
        constitutional_halt(f"ADR not found: {adr_id}")

    # -----------------------------------------------------------------
    # 3. Advance epoch (intentional identity divergence)
    # -----------------------------------------------------------------
    current_epoch = registry["epoch"]["current"]
    new_epoch = current_epoch + 1
    now = datetime.datetime.utcnow().isoformat() + "Z"

    registry["epoch"]["current"] = new_epoch
    registry["epoch"]["last_advanced_by"] = adr_id
    registry["epoch"]["advanced_at"] = now

    # Explicitly unseal to allow lawful mutation
    registry["attestation"]["seal_status"] = "UNSEALED"

    with open(registry_path, "w") as f:
        yaml.safe_dump(registry, f, sort_keys=False)

    # -----------------------------------------------------------------
    # 4. Record immutable epoch history (pre‑reseal)
    # -----------------------------------------------------------------
    history_dir.mkdir(exist_ok=True)

    history_record = {
        "schema": "afritech.registry.history.v1",
        "epoch": {
            "number": new_epoch,
            "parent": current_epoch,
            "status": "FINAL",
            "monotonic": True,
        },
        "authority": {
            "adr": adr_id,
        },
        "timestamp": {
            "enacted_at": now,
        },
        "sealing": {
            "pre_state": "SEALED",
            "unsealed_for_mutation": True,
            "resealed": False,
        },
        "violations": {
            "detected": False,
        },
    }

    history_path = history_dir / f"epoch_{new_epoch}.yaml"
    with open(history_path, "w") as f:
        yaml.safe_dump(history_record, f, sort_keys=False)

    # -----------------------------------------------------------------
    # 5. Reseal registry (recomputes ALL manifest hashes)
    # -----------------------------------------------------------------
    seal_registry()

    # -----------------------------------------------------------------
    # 6. Final confirmation
    # -----------------------------------------------------------------
    print(f"🟢 Epoch advanced: {current_epoch} → {new_epoch}")
    print(f"📜 Authority: {adr_id}")
    print("🔏 Registry resealed")


    # -----------------------------------------------------------------
    # 7. Emit non-authoritative audit event (best effort)
    # -----------------------------------------------------------------
    emit_event(
        event_type="epoch_advanced",
        severity_class="informational",
        epoch=new_epoch,
        adr=adr_id,
        description=(
            f"Epoch advanced from {current_epoch} to {new_epoch}  "#by {adr_id}.\n"
            f"under authority {adr_id}. \n" 
            f"Registry resealed under new epoch identity."
        ),
    )


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        constitutional_halt("Usage: advance_epoch.py ADR-XXXX")

    advance_epoch(sys.argv[1])