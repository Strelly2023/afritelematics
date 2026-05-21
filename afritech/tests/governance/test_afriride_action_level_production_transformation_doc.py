from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Action_Level_Production_Transformation_Plan.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: ACTION-LEVEL PRODUCTION HARDENING ROADMAP",
    "CLASSIFICATION: ISOLATED OPERATIONAL ROADMAP SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "replay authority",
    "execution legality",
    "core invariants",
    "identity ontology",
    "claim admissibility",
    "operational deployment proof",
)

TWO_WORLDS = (
    "World A - Truth Engine",
    "World B - Production System",
    "Production System\n-> Adapter and Control Layer\n-> AfriTech Core",
)

MVP_KERNEL = (
    "1 API service",
    "1 queue",
    "1 worker",
    "1 event store",
    "1 read database",
    "Worker is the only production component allowed to call the AfriTech core.",
)

LEDGER_FIELDS = (
    "event_id",
    "operation",
    "input",
    "normalized_input",
    "output",
    "trace",
    "replay_hash",
    "timestamp",
    "sequence_id",
    "partition_id",
)

FORBIDDEN_INFLATION = (
    "afriride is production-ready",
    "production deployment readiness achieved",
    "global marketplace readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale dispatch guarantees achieved",
    "multi-region commercial readiness achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_action_level_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not runtime authority" in lowered
    assert "not evidence of production deployment" in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_action_level_plan_preserves_two_world_separation() -> None:
    text = read_doc()

    for phrase in TWO_WORLDS:
        assert phrase in text

    for core_property in (
        "deterministic",
        "replayable",
        "invariant-bound",
        "closed-world",
        "constitutionally governed",
    ):
        assert core_property in text

    for production_surface in (
        "APIs",
        "queues",
        "workers",
        "mobile requests",
        "maps adapters",
        "payments adapters",
        "scaling infrastructure",
        "observability",
    ):
        assert production_surface in text

    assert "Production is controlled adaptation." in text
    assert "Core is preserved truth." in text


def test_action_level_plan_defines_minimal_production_kernel() -> None:
    text = read_doc()

    for phrase in MVP_KERNEL:
        assert phrase in text

    for stack_item in (
        "Django",
        "FastAPI",
        "AWS SQS",
        "Kafka",
        "NATS",
        "PostgreSQL",
        "append-only event_log table",
    ):
        assert stack_item in text

    assert (
        "User request\n-> API\n-> Queue\n-> Worker\n-> AfriTech Core"
        in text
    )


def test_action_level_plan_defines_replay_ledger() -> None:
    text = read_doc()

    assert "event_log table" in text

    for field in LEDGER_FIELDS:
        assert field in text

    for responsibility in (
        "audit trail",
        "debugging",
        "compliance evidence",
        "rollback analysis",
        "replay validation",
        "continuity recovery",
    ):
        assert responsibility in text

    assert "does not replace constitutional proof authority" in text


def test_action_level_plan_defines_normalization_and_recorded_inputs() -> None:
    text = read_doc()

    assert "External Input\n-> Normalize\n-> Canonical Input" in text

    for noisy_input in (
        "inconsistent",
        "delayed",
        "duplicated",
        "unordered",
        "noisy",
        "provider-dependent",
    ):
        assert noisy_input in text

    for normalized_output in (
        "canonical grid point",
        "canonical sequence_id",
        "recorded observation timestamp",
        "source adapter version",
        "replay-safe payload hash",
    ):
        assert normalized_output in text

    assert "Convert real-world noise into deterministic input." in text


def test_action_level_plan_defines_deterministic_scaling() -> None:
    text = read_doc()

    assert "events\n-> validate\n-> deduplicate\n-> order\n-> execute" in text
    assert "partition_key = city_id" in text

    for partition_boundary in (
        "own queue",
        "own worker group",
        "own ordering constraints",
        "own dead-letter queue",
        "own replay recovery boundary",
    ):
        assert partition_boundary in text

    for result in (
        "horizontal scaling",
        "deterministic execution",
        "failure isolation",
        "replay-safe recovery",
    ):
        assert result in text


def test_action_level_plan_defines_external_integration_contracts() -> None:
    text = read_doc()

    for provider in (
        "Google Maps",
        "Mapbox",
        "OpenStreetMap",
        "Stripe",
        "M-Pesa",
        "Flutterwave",
        "Paystack",
    ):
        assert provider in text

    assert "External systems are input streams, not constitutional dependencies." in text
    assert "call provider\n-> store response\n-> normalize response" in text

    for adapter in (
        "maps_adapter_v1",
        "payments_adapter_v1",
        "gps_adapter_v1",
        "notification_adapter_v1",
        "identity_adapter_v1",
    ):
        assert adapter in text

    for adapter_field in (
        "input schema",
        "normalization rules",
        "recorded response schema",
        "failure behavior",
        "replay behavior",
        "idempotency requirements",
    ):
        assert adapter_field in text


def test_action_level_plan_defines_product_ux_and_performance_rules() -> None:
    text = read_doc()

    for module in (
        "deterministic matching engine",
        "trip lifecycle orchestration",
        "pricing engine",
        "notification service",
        "payment coordination service",
        "driver availability service",
        "rider request service",
        "admin operations console",
    ):
        assert module in text

    for ui_rule in (
        "submit intent",
        "show pending state",
        "poll or subscribe to confirmed state",
        "render replay-confirmed result",
    ):
        assert ui_rule in text

    assert "truth: event log" in text
    assert "fast reads: materialized views and caches" in text

    for snapshot_rule in (
        "bind to event offset",
        "include replay hash",
        "include schema version",
        "remain rebuildable from events",
        "never replace source events",
    ):
        assert snapshot_rule in text


def test_action_level_plan_defines_deployment_sequence_and_deliverables() -> None:
    text = read_doc()

    for phase in (
        "Phase A - Local Production Pilot",
        "Phase B - Controlled Regional Rollout",
        "Phase C - Multi-Region Expansion",
        "Phase D - Scale Optimization",
    ):
        assert phase in text

    for step in (
        "Step 1 - Add Adapter Layer",
        "Step 2 - Introduce Queue-Based Execution",
        "Step 3 - Add Replay Ledger",
        "Step 4 - Normalize External Inputs",
        "Step 5 - Partition Execution",
        "Step 6 - Scale Workers",
        "Step 7 - Integrate External Systems via Recording",
        "Step 8 - Build Product Features",
    ):
        assert step in text

    for deliverable in (
        "adapter contract schema",
        "idempotency keys",
        "ledger schema",
        "canonical sequence assignment",
        "partition replay boundary",
        "worker health checks",
        "provider replay tests",
        "driver acceptance flow",
    ):
        assert deliverable in text


def test_action_level_plan_preserves_validation_gates_and_safe_classification() -> None:
    text = read_doc()

    for gate in (
        "python3 -m afritech.ci.constitutional_pipeline",
        "python3 -m afritech.ci.claim_discipline_validator",
        "python3 -m afritech.verify.replay",
        "python3 -m afritech.demo.proof",
        "pytest -q",
    ):
        assert gate in text

    for production_test in (
        "adapter contract tests",
        "event schema compatibility tests",
        "queue ordering tests",
        "idempotency tests",
        "snapshot replay tests",
        "recorded input replay tests",
        "load tests",
        "security scans",
        "rollback tests",
        "incident runbook drills",
    ):
        assert production_test in text

    assert "scaling controlled access to a deterministic constitutional core" in text
    assert "without redefining AfriTech truth" in text
