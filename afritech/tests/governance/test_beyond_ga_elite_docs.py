from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_staging_runbook_covers_secrets_public_endpoint_and_remote_verification() -> None:
    text = read("docs/operations/AFRITECH_STAGING_DEPLOYMENT_AND_PARTNER_DEMO_RUNBOOK.md")

    for required in (
        "Staging environment",
        "Real secrets",
        "Remote verification",
        "Controlled public endpoint",
        "Real partner demo",
        "./scripts/run_remote_afritech_verification.sh",
    ):
        assert required in text


def test_enterprise_and_market_docs_cover_required_beyond_ga_topics() -> None:
    readiness = read("docs/strategy/AFRITECH_ENTERPRISE_READINESS_REVIEW.md")
    monetization = read("docs/strategy/AFRITECH_MONETIZATION_AND_ECOSYSTEM_EXPANSION_BLUEPRINT.md")
    architecture = read("docs/architecture/AFRITECH_LIVE_DEPLOYMENT_ARCHITECTURE_MULTI_CLOUD.md")

    for required in ("investors", "governments", "enterprise partners", "public verification endpoint"):
        assert required.lower() in readiness.lower()

    for required in ("verification API usage", "network effect", "public verification endpoint"):
        assert required.lower() in monetization.lower()

    for required in ("AWS", "GCP", "Azure", "/public/verify/{anchor_id}", "/v1/ops/observability/dashboard"):
        assert required in architecture
