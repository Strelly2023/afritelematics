# afritech/verify/verify_replay_witness.py

"""
AfriTech Replay Witness Verifier
================================

Verifies that a replay witness binds replay legitimacy
to constitutional execution legitimacy.

FAIL‑CLOSED.
"""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

WITNESS = ROOT / "afritech/proof/replay_witness.json"

RUNTIME_CERT = ROOT / "afritech/proof/runtime_certificate.json"
INVARIANT_IR = ROOT / "afritech/constitution/compiled/invariants_ir.json"
EPOCH_IR = ROOT / "afritech/epoch/compiled/epoch_ir.json"
REPLAY_TRACE = ROOT / "afritech/replay/replay_trace.json"


def fail(msg: str) -> None:
    print(f"[REPLAY VERIFICATION FAILURE] {msg}", file=sys.stderr)
    sys.exit(1)


def sha256_file(path: Path) -> str:
    if not path.exists():
        fail(f"Missing artifact: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if not WITNESS.exists():
        fail("Missing replay witness")

    witness = json.loads(WITNESS.read_text(encoding="utf-8"))

    expected = {
        "runtime_certificate_hash": sha256_file(RUNTIME_CERT),
        "invariant_ir_hash": sha256_file(INVARIANT_IR),
        "epoch_ir_hash": sha256_file(EPOCH_IR),
        "replay_trace_hash": sha256_file(REPLAY_TRACE),
    }

    for field, value in expected.items():
        if witness.get(field) != value:
            fail(f"Replay witness mismatch: {field}")

    if not witness.get("valid", False):
        fail("Replay witness marked invalid")

    print("✅ Replay witness verified — replay is constitutionally valid")


if __name__ == "__main__":
    main()