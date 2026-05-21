from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_AWS_Deployment_Plan.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: CLOUD DEPLOYMENT ROADMAP",
    "CLASSIFICATION: ISOLATED OPERATIONAL DEPLOYMENT SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "execution legality",
    "core invariants",
    "identity ontology",
    "claim admissibility",
    "production deployment proof",
)

AWS_SERVICES = (
    "Amazon API Gateway",
    "AWS Lambda",
    "Amazon SQS",
    "Amazon ECS Fargate",
    "Amazon RDS PostgreSQL",
    "DynamoDB",
    "ElastiCache",
    "CloudWatch",
)

FORBIDDEN_INFLATION = (
    "aws deployment completed",
    "afriride production readiness achieved",
    "global marketplace readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale dispatch guarantees achieved",
    "pci compliance achieved",
    "soc 2 compliance achieved",
    "multi-region commercial readiness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_aws_deployment_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence that AfriRide is already deployed on AWS".lower() in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered.split("# 14. bounded non-claims")[0]


def test_aws_deployment_plan_maps_local_mvp_to_cloud_surfaces() -> None:
    text = read_doc()

    for service in AWS_SERVICES:
        assert service in text

    for local_surface in (
        "FastAPI TestClient API",
        "in-process partitioned queue",
        "WorkerPool",
        "in-memory event log",
        "replay engine",
    ):
        assert local_surface in text

    for cloud_surface in (
        "API Gateway plus Lambda",
        "SQS queues by partition",
        "ECS Fargate worker service",
        "RDS PostgreSQL event_log",
        "Lambda or scheduled batch replay job",
    ):
        assert cloud_surface in text


def test_aws_deployment_plan_preserves_core_invocation_boundary() -> None:
    text = read_doc()

    assert "Only declared workers may invoke the AfriTech core." in text
    assert "External clients may only submit normalized-admissible requests" in text
    assert "API execution role must not" in text
    assert "invoke the deterministic core directly" in text
    assert "Worker execution role must not" in text
    assert "accept raw external HTTP input" in text


def test_aws_deployment_plan_defines_partitioned_sqs_and_worker_semantics() -> None:
    text = read_doc()

    for queue in (
        "afriride-partition-0",
        "afriride-partition-7",
        "afriride-partition-0-dlq",
    ):
        assert queue in text

    for routing_key in ("city_id", "trip_id", "request_id", "user_id"):
        assert routing_key in text

    for worker_step in (
        "receive normalized event",
        "validate edge trace",
        "invoke deterministic core",
        "generate replay_hash",
        "append event_log record",
        "delete SQS message only after successful event_log write",
    ):
        assert worker_step in text


def test_aws_deployment_plan_defines_event_log_replay_and_observability() -> None:
    text = read_doc()

    for schema_token in (
        "CREATE TABLE event_log",
        "request_id TEXT NOT NULL",
        "partition_id INTEGER NOT NULL",
        "normalized_input JSONB NOT NULL",
        "replay_hash TEXT NOT NULL",
    ):
        assert schema_token in text

    assert "event_log is an operational replay ledger" in text
    assert "does not replace constitutional proof authority" in text

    for replay_step in (
        "load event_log rows",
        "re-execute deterministic core over normalized_input",
        "recalculate replay_hash",
        "fail loudly on mismatch",
    ):
        assert replay_step in text

    for metric in (
        "SQS queue depth per partition",
        "worker failure count",
        "event_log write failures",
        "replay mismatch count",
        "dead-letter queue count",
    ):
        assert metric in text


def test_aws_deployment_plan_defines_security_and_acceptance_test() -> None:
    text = read_doc()

    for security in (
        "AWS Secrets Manager",
        "SSM Parameter Store",
        "least-privilege policies",
        "WAF on public API",
        "idempotency keys",
        "RDS encryption at rest",
        "SQS encryption",
    ):
        assert security in text

    for acceptance_step in (
        "POST /process through API Gateway",
        "API returns status accepted",
        "Correct SQS partition receives normalized message",
        "ECS worker consumes message",
        "Worker writes RDS event_log row",
        "Replay verification passes",
    ):
        assert acceptance_step in text
