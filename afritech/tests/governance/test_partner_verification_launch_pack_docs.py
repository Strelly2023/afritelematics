from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PARTNER_DOC = ROOT / "docs/architecture/AFRIRIDE_PARTNER_VERIFICATION_AND_ANCHOR_PIPELINE.md"
LAUNCH_PACK = ROOT / "docs/operations/AFRIRIDE_PRODUCTION_LAUNCH_READINESS_PACK.md"


def test_partner_verification_doc_defines_api_sdk_and_anchor_pipeline() -> None:
    text = PARTNER_DOC.read_text(encoding="utf-8")

    for item in (
        "PARTNER VERIFICATION API AND ANCHOR PUBLICATION PIPELINE",
        "POST /v1/partner/verify",
        "GET /v1/partner/anchors/{anchor_id}",
        "PartnerVerificationClient",
        "trace_hash + replay_hash + receipt_hash -> external anchor commitment",
        "publication target",
        "multi-region publisher lanes",
        "publication failure opens evidence-complete alert",
        "The anchor proves export integrity. Replay remains the authority.",
    ):
        assert item in text


def test_launch_readiness_pack_covers_partner_anchors_and_operational_alerting() -> None:
    text = LAUNCH_PACK.read_text(encoding="utf-8")

    for item in (
        "STATUS: PRODUCTION LAUNCH READINESS PACK",
        "ENTERPRISE_GATED_LAUNCH_PACK",
        "This pack is a launch decision surface, not a source of truth.",
        "Replay remains the authority.",
        "partner verification API evidence",
        "anchor publication pipeline evidence",
        "real-time anomaly alerting service",
        "multi-region failover drill evidence",
        "executive go/no-go signoff",
        "launch success is guaranteed",
    ):
        assert item in text
