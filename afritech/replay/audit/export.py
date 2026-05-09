"""
afritech/replay/audit/export.py

JSON audit export for replay verifier results.

Purpose:
- Emit machine-readable verifier outcomes
- Preserve stdout purity for constitutional evidence
- Enable CI, archival, and compliance tooling

IMPORTANT:
- This module must NEVER write to stdout.
- All audit output is side-channel only (file-based).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import time


# ============================================================
# AUDIT EXPORT (PUBLIC API)
# ============================================================

def export_verifier_audit(
    *,
    output_dir: str,
    transcript_path: str,
    request_hash: str,
    verdict: Any,
) -> Path:
    """
    Export a verifier result as a JSON audit artifact.

    Parameters:
      output_dir     : Directory where audit file is written
      transcript_path: Path of transcript under verification
      request_hash   : Canonical request hash
      verdict        : ReplayVerdict object

    Returns:
      Path to the generated JSON audit file
    """

    audit_dir = Path(output_dir)
    audit_dir.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time())

    audit_payload = {
        "audit_version": "1.0.0",
        "generated_at": timestamp,

        "inputs": {
            "transcript_path": transcript_path,
            "request_hash": request_hash,
        },

        "verdict": {
            "status": verdict.status,
            "replay_hash": verdict.replay_hash,
            "failure_mode": verdict.failure_mode,
            "violated_invariant": verdict.violated_invariant,
            "divergence_location": verdict.divergence_location,
        },
    }

    filename = f"replay_audit_{timestamp}.json"
    output_path = audit_dir / filename

    output_path.write_text(
        json.dumps(audit_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    return output_path
