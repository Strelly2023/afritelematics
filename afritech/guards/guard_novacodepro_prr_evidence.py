from __future__ import annotations


def verify_prr_requires_signed_evidence(package: dict[str, object]) -> bool:
    return bool(package.get("evidence_manifest_hash")) and package.get("ga_allowed") is False
