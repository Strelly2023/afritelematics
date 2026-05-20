from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Production_Grade_System_Roadmap.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: OPERATIONAL PRODUCTION-READINESS ROADMAP",
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
)

CORE_INVARIANTS = (
    "deterministic execution",
    "replay authority",
    "mutation traceability",
    "closed-world enforcement",
    "canonical identity resolution",
    "claim-evidence-implementation binding",
)

PRODUCTION_PHASES = (
    "Phase 1 - Edge Layer Architecture",
    "Phase 2 - Event-Driven Runtime",
    "Phase 3 - State Store Strategy",
    "Phase 4 - Integration Contracts",
    "Phase 5 - Scaling Strategy",
    "Phase 6 - Product Completion Layer",
)

VALIDATION_GATES = (
    "python3 -m afritech.ci.constitutional_pipeline",
    "python3 -m afritech.ci.claim_discipline_validator",
    "python3 -m afritech.verify.replay",
    "python3 -m afritech.demo.proof",
    "pytest -q",
)

FORBIDDEN_INFLATION = (
    "afriride is production-ready",
    "production deployment readiness achieved",
    "global marketplace readiness achieved",
    "universal fault tolerance achieved",
    "complete state-space exhaustiveness achieved",
    "infinite-scale dispatch guarantees achieved",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_production_roadmap_has_bounded_operational_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not declare afriride production-ready" in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_production_roadmap_preserves_core_boundary() -> None:
    text = read_doc()

    for invariant in CORE_INVARIANTS:
        assert invariant in text

    assert "Core (unchanged) -> Adapter Layer -> External World" in text

    for forbidden_core_input in (
        "raw HTTP",
        "system-clock authority",
        "external randomness",
        "unrecorded API responses",
        "unbounded GPS noise",
        "observer-relative state",
    ):
        assert forbidden_core_input in text


def test_production_roadmap_defines_required_phases() -> None:
    text = read_doc()

    for phase in PRODUCTION_PHASES:
        assert phase in text

    assert "RAW INPUT -> Adapter -> Normalization -> Core" in text
    assert "External Event\n-> Queue\n-> Deterministic Ordering" in text
    assert "Event Log -> Snapshot -> Replay Delta" in text


def test_production_roadmap_defines_adapter_and_normalization_rules() -> None:
    text = read_doc()

    for capability in (
        "translate external input into canonical input",
        "normalize GPS and location data",
        "convert async events into ordered deterministic events",
        "record externally supplied values for replay",
        "malformed payloads",
        "undeclared fields",
        "unversioned integration messages",
        "unrecorded external responses",
        "nondeterministic execution inputs",
    ):
        assert capability in text


def test_production_roadmap_defines_event_workers_state_and_snapshots() -> None:
    text = read_doc()

    for worker_property in (
        "stateless",
        "deterministic",
        "idempotency-aware",
        "partition-aware",
        "trace-emitting",
        "hash-emitting",
        "replay-compatible",
    ):
        assert worker_property in text

    for state_rule in (
        "append-only",
        "replayable",
        "tamper-evident",
        "rebuildable from events",
        "non-authoritative over replay",
        "snapshot must bind to event offset",
        "snapshot must include replay hash",
        "snapshot must not replace source events",
    ):
        assert state_rule in text


def test_production_roadmap_defines_integration_contracts_and_recorded_inputs() -> None:
    text = read_doc()

    for adapter in (
        "maps_adapter_v1",
        "payments_adapter_v1",
        "gps_adapter_v1",
        "notification_adapter_v1",
        "identity_adapter_v1",
    ):
        assert adapter in text

    assert "external_input = recorded_input" in text

    for recorded_input in (
        "GPS reading",
        "map route response",
        "traffic estimate",
        "payment provider response",
        "notification provider response",
        "pricing partner response",
    ):
        assert recorded_input in text

    for mode in ("Strict", "Recorded", "Observational"):
        assert mode in text


def test_production_roadmap_defines_scaling_product_and_deployment_requirements() -> None:
    text = read_doc()

    for scaling_term in (
        "partition_key = city_id",
        "queues per partition",
        "dead-letter queues",
        "replay-safe recovery",
        "replay-confirmed state",
    ):
        assert scaling_term in text

    for product_gap in (
        "full rider app",
        "full driver app",
        "admin operations console",
        "maps adapter",
        "payment adapter",
        "notification adapter",
        "fraud and abuse controls",
        "incident response procedures",
    ):
        assert product_gap in text

    for deployment_requirement in (
        "secrets management",
        "database migrations",
        "queue infrastructure",
        "structured logging",
        "distributed tracing",
        "backup and restore",
        "deployment rollback procedure",
        "runbooks",
    ):
        assert deployment_requirement in text


def test_production_roadmap_preserves_ci_and_readiness_criteria() -> None:
    text = read_doc()

    for gate in VALIDATION_GATES:
        assert gate in text

    for extra_gate in (
        "adapter contract tests",
        "event schema compatibility tests",
        "queue ordering tests",
        "snapshot replay tests",
        "load tests",
        "security scans",
        "rollback tests",
    ):
        assert extra_gate in text

    for criterion in (
        "edge adapters are declared and versioned",
        "normalization gate is enforced",
        "external nondeterminism is recorded",
        "event queue ordering is deterministic per partition",
        "executor workers are stateless and replay-compatible",
        "event log is append-only and replayable",
        "materialized state is rebuildable",
        "constitutional pipeline remains canonical",
        "claim discipline remains enforced",
    ):
        assert criterion in text


def test_production_roadmap_has_safe_current_and_final_classifications() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "validated deterministic lifecycle behavior and production-readiness" in lowered
    assert "requirements defined" in lowered

    for not_claimed in (
        "production deployment readiness",
        "global marketplace readiness",
        "universal fault tolerance",
        "complete state-space exhaustiveness",
        "infinite-scale dispatch guarantees",
    ):
        assert not_claimed in lowered

    assert "bounded operational roadmap" in lowered
    assert "without redefining afritech constitutional truth" in lowered
    assert "admissibility authority" in lowered
