"""Public trust badge payloads derived from the signed feature registry."""

from __future__ import annotations

from typing import Any

from afritech.features import feature_by_id, registry_payload
from afritech.tools.feature_registry_verifier import verify_registry_payload


BADGE_CLASSIFICATION = "AFRITECH_PUBLIC_TRUST_BADGE"
BADGE_LABEL = "Verified by AfriTech Trust Layer"
BADGE_AUTHORITY_BOUNDARY = (
    "badge_displays_verified_registry_evidence_without_creating_runtime_production_or_payment_authority"
)


def build_trust_badge(
    feature_id: str | None = None,
    *,
    public_base_url: str = "https://afritechnology.com",
) -> dict[str, Any]:
    registry = registry_payload()
    verification = verify_registry_payload(registry)
    selected_feature = None
    if feature_id is not None:
        selected_feature = feature_by_id(feature_id).canonical_dict()

    proof_path = (
        f"/public/trust-badge/{feature_id}"
        if feature_id is not None
        else "/public/trust-badge"
    )
    verification_url = f"{public_base_url.rstrip('/')}{proof_path}"
    return {
        "classification": BADGE_CLASSIFICATION,
        "label": BADGE_LABEL,
        "status": "VERIFIED" if verification["verified"] else "REVIEW_REQUIRED",
        "verified": verification["verified"],
        "registry_hash": registry["registry_hash"],
        "feature_id": feature_id,
        "feature": selected_feature,
        "production_ready_feature_count": registry["production_ready_feature_count"],
        "production_ready_feature_ids": registry["production_ready_feature_ids"],
        "verified_true": verification["verified_true"],
        "public_proof_url": verification_url,
        "embed": {
            "html": (
                f'<a href="{verification_url}" rel="noopener">'
                f'{BADGE_LABEL}</a>'
            ),
            "text": f"{BADGE_LABEL} - public proof: {verification_url}",
        },
        "links": {
            "registry": "/public/feature-registry",
            "registry_verification": "/public/feature-registry/verify",
            "trust_badge": proof_path,
            "ecosystem_portal": "/public/ecosystem-evolution/portal",
            "system_integrity": "/public/ecosystem-evolution/verify",
        },
        "authority_boundary": BADGE_AUTHORITY_BOUNDARY,
    }


def verify_trust_badge(badge: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = badge or build_trust_badge()
    registry_verification = verify_registry_payload(registry_payload())
    verified = (
        payload.get("classification") == BADGE_CLASSIFICATION
        and payload.get("label") == BADGE_LABEL
        and payload.get("verified") is True
        and payload.get("verified_true") is True
        and payload.get("registry_hash") == registry_verification["registry_hash"]
        and payload.get("authority_boundary") == BADGE_AUTHORITY_BOUNDARY
        and registry_verification["verified"] is True
    )
    return {
        "verified": verified,
        "classification": payload.get("classification"),
        "label": payload.get("label"),
        "registry_hash": payload.get("registry_hash"),
        "registry": registry_verification,
        "public_proof_url": payload.get("public_proof_url"),
        "authority_boundary": payload.get("authority_boundary"),
    }


__all__ = [
    "BADGE_AUTHORITY_BOUNDARY",
    "BADGE_CLASSIFICATION",
    "BADGE_LABEL",
    "build_trust_badge",
    "verify_trust_badge",
]
