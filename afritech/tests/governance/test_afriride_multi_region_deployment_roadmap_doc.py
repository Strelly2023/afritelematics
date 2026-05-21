from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Multi_Region_Deployment_Roadmap.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: MULTI-REGION DEPLOYMENT ROADMAP",
    "CLASSIFICATION: ISOLATED OPERATIONAL DEPLOYMENT SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

FORBIDDEN_INFLATION = (
    "multi-region deployment active",
    "africa-scale readiness achieved",
    "global high availability proven",
    "cross-region failover proven",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale dispatch guarantees achieved",
    "commercial multi-region readiness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_multi_region_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence that AfriRide is already deployed across multiple regions".lower() in lowered
    assert "does not redefine" in lowered
    assert "multi-region readiness proof" in text

    before_non_claims = lowered.split("# 10. bounded non-claims")[0]
    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in before_non_claims


def test_multi_region_plan_preserves_independent_regional_systems() -> None:
    text = read_doc()

    assert "Each region is an independent deterministic system." in text
    assert "Cross-region coordination replicates events, not mutable live state." in text
    assert "Sydney" in text
    assert "Johannesburg" in text
    assert "Nairobi" in text

    for regional_surface in (
        "API Gateway endpoint",
        "Lambda API adapter",
        "SQS partition queues",
        "ECS worker pool",
        "RDS event_log",
        "regional replay job",
    ):
        assert regional_surface in text


def test_multi_region_plan_defines_routing_partitioning_and_replication() -> None:
    text = read_doc()

    for routing in (
        "Route53 latency routing",
        "Route53 failover routing",
        "regional API Gateway endpoints",
    ):
        assert routing in text

    for partition_key in (
        "region_key = continent or aws_region",
        "partition_key = city_id",
        "fallback_partition_key = trip_id",
        "identity_key = request_id",
    ):
        assert partition_key in text

    for replication in (
        "SNS to SQS fanout",
        "EventBridge cross-region event bus",
        "Kafka MirrorMaker",
        "RDS logical replication",
        "S3 event archive replication",
    ):
        assert replication in text


def test_multi_region_plan_defines_replay_and_failover_boundaries() -> None:
    text = read_doc()

    for replay_mode in (
        "replay(local events)",
        "replay(imported events)",
        "hash equivalence",
        "duplicate event detection",
        "import completeness",
    ):
        assert replay_mode in text

    for failover_step in (
        "Detect regional failure.",
        "Freeze new local admission for unhealthy region.",
        "Route new traffic through Route53 to healthy region.",
        "Replay imported events.",
        "Resume admitted operations only after replay verification passes.",
    ):
        assert failover_step in text

    assert "Replay mismatch invalidates operational failover eligibility." in text
    assert "manual event_log rewriting" in text
