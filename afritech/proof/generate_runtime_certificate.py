# afritech/proof/generate_runtime_certificate.py

"""
AfriTech Runtime Certificate Generator
=====================================

Materializes the runtime certificate as a canonical JSON artifact.

GENERATED OUTPUT (DO NOT EDIT):
- afritech/proof/runtime_certificate.json

CONSTITUTIONAL RULE:
Runtime legitimacy MUST be materialized as a deterministic,
hashable artifact before replay binding is allowed.

FAIL-CLOSED.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any

from afritech.proof.build_certificate import build_runtime_certificate


# ---------------------------------------------------------------------
# PATHS (CANONICAL)
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "afritech" / "proof" / "runtime_certificate.json"
TMP_OUTPUT = OUTPUT.with_suffix(".json.tmp")


# ---------------------------------------------------------------------
# FAILURE
# ---------------------------------------------------------------------

def fail(msg: str) -> None:
    print(f"[RUNTIME CERTIFICATE FAILURE] {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    """
    Build and persist the runtime certificate.

    This is the ONLY code path allowed to create
    runtime_certificate.json.
    """

    # -------------------------------------------------------------
    # BUILD CERTIFICATE (IN-MEMORY)
    # -------------------------------------------------------------

    try:
        cert = build_runtime_certificate()
    except Exception as e:
        fail(f"Certificate construction failed: {e}")

    # -------------------------------------------------------------
    # SERIALIZE
    # -------------------------------------------------------------

    try:
        data: Dict[str, Any] = cert.to_dict()
    except Exception as e:
        fail(f"Certificate serialization failed: {e}")

    # -------------------------------------------------------------
    # WRITE ATOMICALLY
    # -------------------------------------------------------------

    try:
        TMP_OUTPUT.write_text(
            json.dumps(data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        TMP_OUTPUT.replace(OUTPUT)
    except Exception as e:
        fail(f"Failed to write runtime certificate: {e}")

    # -------------------------------------------------------------
    # SUCCESS
    # -------------------------------------------------------------

    print("✅ Runtime certificate generated")
    print(f"   Output: {OUTPUT.relative_to(ROOT)}")


# ---------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------

if __name__ == "__main__":
    main()