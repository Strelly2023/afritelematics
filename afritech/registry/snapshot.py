"""Signed immutable snapshots for the feature registry."""

from __future__ import annotations

import json
from pathlib import Path

from afritech.features import ROOT, generate_claim_snapshot
from afritech.security.signing import public_key_hex, sign_registry, signer_id, verify_signature


SNAPSHOT_DIR = ROOT / "reports/registry_snapshots"


def generate_snapshot(version: str = "v1") -> dict[str, object]:
    snapshot = generate_claim_snapshot(version)
    signature = sign_registry(str(snapshot["registry_hash"]))
    snapshot["signature"] = {
        "algorithm": "Ed25519",
        "signer_id": signer_id(),
        "public_key": public_key_hex(),
        "scope": "registry_hash",
        "value": signature,
        "trust_chain": ("AFRITECH_CORE", "REGISTRY_SIGNER", "VALIDATOR"),
    }
    snapshot["signed"] = True
    return snapshot


def write_snapshot(version: str = "v1") -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = SNAPSHOT_DIR / f"{version}.json"
    path.write_text(
        json.dumps(generate_snapshot(version), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def load_snapshot(version: str = "v1") -> dict[str, object]:
    path = SNAPSHOT_DIR / f"{version}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def verify_snapshot(snapshot: dict[str, object]) -> dict[str, object]:
    signature = snapshot.get("signature", {})
    if not isinstance(signature, dict):
        return {"verified": False, "reason": "missing_signature"}
    public_key = signature.get("public_key")
    signature_value = signature.get("value")
    registry_hash = snapshot.get("registry_hash")
    if not all(isinstance(value, str) for value in (public_key, signature_value, registry_hash)):
        return {"verified": False, "reason": "invalid_signature_payload"}
    verified = verify_signature(public_key, signature_value, registry_hash)
    return {
        "verified": verified,
        "classification": snapshot.get("classification"),
        "status": snapshot.get("status"),
        "generation_mode": snapshot.get("generation_mode"),
        "registry_hash": registry_hash,
        "signature_algorithm": signature.get("algorithm"),
        "production_ready_feature_count": snapshot.get("production_ready_feature_count"),
        "live_pilot_authorized": snapshot.get("live_pilot_authorized"),
        "production_proven": snapshot.get("production_proven"),
    }


__all__ = [
    "SNAPSHOT_DIR",
    "generate_snapshot",
    "load_snapshot",
    "verify_snapshot",
    "write_snapshot",
]
