"""Verifier for signed feature-registry payloads and snapshots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import request

from afritech.features import registry_payload
from afritech.registry.snapshot import load_snapshot, verify_snapshot
from afritech.security.signing import verify_signature
from afritech.security.trust_registry import signer_authorized


def load_registry_source(source: str | None = None) -> dict[str, Any]:
    if source is None:
        return registry_payload()
    if source.startswith(("http://", "https://")):
        with request.urlopen(source, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    else:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("registry source must decode to a JSON object")
    return payload


def verify_registry_payload(payload: dict[str, Any]) -> dict[str, Any]:
    signature = payload.get("signature")
    registry_hash = payload.get("registry_hash")
    features = payload.get("features")
    if not isinstance(signature, dict) or not isinstance(registry_hash, str):
        return _failure(payload, "missing_registry_signature")
    if not isinstance(features, list):
        return _failure(payload, "missing_features")

    public_key = signature.get("public_key")
    signature_value = signature.get("value")
    signature_valid = (
        isinstance(public_key, str)
        and isinstance(signature_value, str)
        and verify_signature(public_key, signature_value, registry_hash)
    )
    signer_trusted = signer_authorized(payload)
    no_incomplete = payload.get("incomplete_feature_ids") == []
    no_fake = payload.get("feature_count") == len(features)
    no_unverifiable = all(feature.get("evidence_complete") is True for feature in features)
    no_false_production = (
        payload.get("production_ready_feature_count") == 0
        and payload.get("production_proven") is False
        and payload.get("live_pilot_authorized") is False
        and payload.get("economic_activation_allowed") is False
    )

    verified = all(
        (
            signature_valid,
            signer_trusted,
            no_incomplete,
            no_fake,
            no_unverifiable,
            no_false_production,
        )
    )
    return {
        "verified": verified,
        "classification": payload.get("classification"),
        "status": payload.get("status"),
        "generation_mode": payload.get("generation_mode"),
        "registry_hash": registry_hash,
        "signature_valid": signature_valid,
        "signer_trusted": signer_trusted,
        "no_fake_feature_can_exist": no_fake,
        "no_incomplete_feature_can_appear": no_incomplete,
        "no_unverifiable_claim_can_be_exported": no_unverifiable,
        "no_production_state_can_be_falsely_implied": no_false_production,
        "feature_count": payload.get("feature_count"),
        "candidate_feature_count": payload.get("candidate_feature_count"),
        "production_ready_feature_count": payload.get("production_ready_feature_count"),
    }


def verify_registry(source: str | None = None) -> dict[str, Any]:
    return verify_registry_payload(load_registry_source(source))


def verify_registry_snapshot(version: str = "v1") -> dict[str, object]:
    return verify_snapshot(load_snapshot(version))


def _failure(payload: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "verified": False,
        "reason": reason,
        "classification": payload.get("classification"),
        "status": payload.get("status"),
        "generation_mode": payload.get("generation_mode"),
    }


__all__ = [
    "load_registry_source",
    "verify_registry",
    "verify_registry_payload",
    "verify_registry_snapshot",
]
