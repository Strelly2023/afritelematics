"""AfriRide mobile release readiness contract helpers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS_PATH = ROOT / "docs/mobile/release/afriride_mobile_release_readiness.json"


def _json_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json(relative_or_absolute: str | Path) -> dict[str, Any]:
    path = Path(relative_or_absolute)
    if not path.is_absolute():
        path = ROOT / path
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"release manifest must be a JSON object: {path}")
    return payload


def _file_hash(relative_path: str) -> str:
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest()


def build_afriride_mobile_release_readiness() -> dict[str, Any]:
    contract = _read_json(READINESS_PATH)
    app_manifests = [_read_json(path) for path in contract["apps"]]
    required_docs = [
        {
            "path": path,
            "sha256": _file_hash(path),
        }
        for path in contract["required_docs"]
    ]
    readiness_payload = {
        "contract": contract,
        "apps": app_manifests,
        "required_docs": required_docs,
    }
    blocking_findings: list[dict[str, str]] = []
    for manifest in app_manifests:
        if not manifest.get("required_capabilities"):
            blocking_findings.append(
                {
                    "code": "MISSING_APP_CAPABILITIES",
                    "app_id": str(manifest.get("app_id")),
                }
            )
        if not manifest.get("release_gates"):
            blocking_findings.append(
                {
                    "code": "MISSING_RELEASE_GATES",
                    "app_id": str(manifest.get("app_id")),
                }
            )

    return {
        "classification": contract["classification"],
        "status": contract["status"] if not blocking_findings else "BLOCKED",
        "release_mode": contract["release_mode"],
        "production_claim_allowed": bool(contract["production_claim_allowed"]),
        "readiness_hash": _json_hash(readiness_payload),
        "apps": app_manifests,
        "required_docs": required_docs,
        "required_validators": contract["required_validators"],
        "release_tracks": contract["release_tracks"],
        "production_blockers": contract.get("production_blockers", []),
        "blocking_findings": blocking_findings,
        "authority_boundary": contract["authority_boundary"],
    }


__all__ = ["build_afriride_mobile_release_readiness"]
