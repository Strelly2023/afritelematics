from __future__ import annotations


def verify_executive_approval_requires_prr(payload: dict[str, object]) -> bool:
    return bool(payload.get("prr_id")) and bool(payload.get("evidence_package_hash")) and payload.get("ga_allowed") is not True
