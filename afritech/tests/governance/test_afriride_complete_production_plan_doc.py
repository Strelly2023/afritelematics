from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriRide_Complete_Production_Readiness_Plan.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: PRODUCTION HARDENING ROADMAP",
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

PRODUCTION_PHASES = (
    "PHASE 1 - Constitutional Stabilization",
    "PHASE 2 - Infrastructure Hardening",
    "PHASE 3 - Database Hardening",
    "PHASE 4 - Real-Time Mobility Infrastructure",
    "PHASE 5 - Mobile Applications",
    "PHASE 6 - Payments Infrastructure",
    "PHASE 7 - Security Hardening",
    "PHASE 8 - Observability and SRE",
    "PHASE 9 - Marketplace Intelligence",
    "PHASE 10 - Compliance and Legal",
    "PHASE 11 - Adversarial Validation",
    "PHASE 12 - Multi-Region Deployment",
)

IMMEDIATE_PRIORITIES = (
    "Priority 1 - Production Database",
    "Priority 2 - Real Mobile Apps",
    "Priority 3 - Production API Layer",
    "Priority 4 - Observability",
    "Priority 5 - Real Payment Integration",
    "Priority 6 - Adversarial Replay Testing",
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


def test_complete_production_plan_has_bounded_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "not yet fully production hardened" in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_complete_production_plan_declares_current_evidence_and_strengths() -> None:
    text = read_doc()

    for evidence in (
        "constitutional validation passed",
        "claim-evidence binding passed",
        "replay validation passed",
        "proof validation passed",
        "AfriRide bounded product tests passed",
    ):
        assert evidence in text

    for strength in (
        "deterministic replay",
        "closed-world execution",
        "identity ontology enforcement",
        "implementation admissibility",
        "witness validation",
        "claim-evidence binding",
        "API idempotency hardening",
    ):
        assert strength in text


def test_complete_production_plan_defines_production_gaps() -> None:
    text = read_doc()

    for gap in (
        "Infrastructure",
        "Security",
        "Scaling",
        "Observability",
        "Payments",
        "Maps",
        "Mobile Apps",
        "Driver Operations",
        "Incident Response",
        "Legal/Compliance",
        "Marketplace Dynamics",
        "Fraud Protection",
        "Data Governance",
    ):
        assert gap in text

    assert "Needs cloud deployment" in text
    assert "Needs enterprise hardening" in text
    assert "Needs real provider integration" in text


def test_complete_production_plan_defines_all_phases() -> None:
    text = read_doc()

    for phase in PRODUCTION_PHASES:
        assert phase in text

    assert "afritech.ci.constitutional_pipeline" in text
    assert "PostgreSQL 16+" in text
    assert "PostGIS" in text
    assert "WebSockets" in text
    assert "Kotlin" in text
    assert "SwiftUI" in text


def test_complete_production_plan_covers_payments_security_observability_and_sre() -> None:
    text = read_doc()

    for payment in ("Stripe", "PayPal", "Flutterwave", "M-Pesa", "Paystack"):
        assert payment in text

    for security in (
        "OAuth2",
        "JWT rotation",
        "MFA",
        "Vault",
        "WAF",
        "SAST",
        "DAST",
        "SBOM generation",
    ):
        assert security in text

    for observability in (
        "Prometheus",
        "Grafana",
        "OpenTelemetry",
        "Jaeger",
        "replay divergence",
        "PagerDuty",
        "SRE runbooks",
    ):
        assert observability in text


def test_complete_production_plan_covers_marketplace_compliance_adversarial_and_multiregion() -> None:
    text = read_doc()

    for capability in (
        "surge pricing",
        "demand forecasting",
        "GPS spoofing detection",
        "terms of service",
        "Australian Privacy Act",
        "PCI DSS",
        "lawful deletion flows",
        "chaos engineering",
        "network partitions",
        "replay mutation attacks",
        "multi-region databases",
        "regional failover",
    ):
        assert capability in text

    for constraint in (
        "replay admissibility",
        "identity determinism",
        "closed-world enforcement",
    ):
        assert constraint in text


def test_complete_production_plan_preserves_immediate_priorities_and_sequence() -> None:
    text = read_doc()

    for priority in IMMEDIATE_PRIORITIES:
        assert priority in text

    for sequence_item in (
        "1. CI consolidation",
        "2. PostgreSQL + PostGIS",
        "3. Mobile apps",
        "4. Real-time geo infrastructure",
        "5. Payments",
        "6. Observability",
        "7. Security hardening",
        "8. Adversarial scaling tests",
        "9. Multi-region deployment",
        "10. Compliance + operational governance",
    ):
        assert sequence_item in text


def test_complete_production_plan_preserves_safe_architecture_and_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    assert "AfriTech Constitutional Core" in text
    assert "Replay / Witness / Governance Layer" in text
    assert "Distributed Marketplace Infrastructure" in text
    assert "Mobile Apps + APIs + Payments + Observability" in text

    assert "deterministic operational legitimacy" in lowered
    assert "ga++++ bounded replay-governed constitutional architecture" in lowered
    assert "production-grade replay-governed mobility platform" in lowered
    assert "bounded hardening program" in lowered
    assert "preserves replay-governed constitutional admissibility" in lowered
