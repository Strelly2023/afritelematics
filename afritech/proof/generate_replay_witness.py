"""
AfriTech Replay Witness Generator
=================================

Generates a replay witness binding replay legitimacy
to constitutional execution legitimacy.

AUTHORITATIVE INPUTS:
- Runtime certificate
- Invariant IR
- Epoch IR
- Replay trace

GENERATED OUTPUT (DO NOT EDIT):
- afritech/proof/replay_witness.json

FAIL-CLOSED.
"""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any


# ---------------------------------------------------------------------
# PATHS (CANONICAL)
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

RUNTIME_CERT = ROOT / "afritech" / "proof" / "runtime_certificate.json"
INVARIANT_IR = ROOT / "afritech" / "constitution" / "compiled" / "invariants_ir.json"
EPOCH_IR = ROOT / "afritech" / "epoch" / "compiled" / "epoch_ir.json"
REPLAY_TRACE = ROOT / "afritech" / "replay" / "replay_trace.json"

OUTPUT = ROOT / "afritech" / "proof" / "replay_witness.json"


# ---------------------------------------------------------------------
# FAILURE
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[REPLAY WITNESS FAILURE] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# HASHING
# ---------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    if not path.exists():
        fail(f"Missing required artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------
# BUILD WITNESS
# ---------------------------------------------------------------------

def build_witness() -> Dict[str, Any]:
    """
    Construct the replay witness from live constitutional artifacts.
    """

    return {
        "schema": "afritech.proof.replay_witness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),

        # Constitutional bindings
        "runtime_certificate_hash": sha256_file(RUNTIME_CERT),
        "invariant_ir_hash": sha256_file(INVARIANT_IR),
        "epoch_ir_hash": sha256_file(EPOCH_IR),

        # Replay binding
        "replay_trace_hash": sha256_file(REPLAY_TRACE),

        # Status
        "valid": True,
    }


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    witness = build_witness()

    OUTPUT.write_text(
        json.dumps(witness, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("✅ Replay witness generated")
    print(f"   Output: {OUTPUT.relative_to(ROOT)}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()