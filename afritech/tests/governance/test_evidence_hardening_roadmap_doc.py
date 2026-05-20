from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/implementation/AfriTech_GA_Elite_Evidence_Hardening_Roadmap.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: HARDENING ROADMAP",
    "CLASSIFICATION: ISOLATED EVIDENCE-PRESSURE SURFACE",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

CURRENT_PROVEN_ITEMS = (
    "constitutional validation execution",
    "claim-evidence binding",
    "claim-implementation binding",
    "replay integrity validation",
    "bounded AfriRide continuity verification",
    "preserve-or-isolate enforcement",
)

VALIDATOR_METRICS = (
    "invariant coverage percent",
    "validator coverage percent",
    "implementation reference coverage percent",
    "claim evidence coverage percent",
    "mutation survival rate",
    "replay divergence detection rate",
)

ADVERSARIAL_ATTEMPTS = (
    "randomized event ordering",
    "illegal import or topology injection",
    "forbidden alias injection",
    "reflection-based access attempts",
    "nondeterministic execution attempts",
    "state mutation attacks",
    "replay divergence injection",
)

CI_COLLAPSE_PROPERTIES = (
    "one canonical CI admissibility gate",
    "every GitHub workflow invokes the canonical gate",
    "every other workflow is classified as wrapper or adapter",
    "no workflow independently defines admissibility",
    "no supporting gate can claim completion without canonical pipeline execution",
)

FORBIDDEN_INFLATION = (
    "validator completeness proven",
    "universal attack resistance proven",
    "final ci collapse complete",
    "global deployment readiness achieved",
    "universal drift impossibility",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start)
    return text[start:end]


def test_evidence_hardening_roadmap_has_isolated_status() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not define proof truth" in text
    assert "does not claim validator completeness" in text
    assert "Evidence hardening must preserve or isolate all claims." in text


def test_evidence_hardening_roadmap_preserves_current_bounded_base() -> None:
    text = read_doc()
    base = section(text, "## Current Proven Base", "## Hardening Objective")

    for item in CURRENT_PROVEN_ITEMS:
        assert item in base

    assert "within the current bounded proof surface" in base
    assert "not universal guarantees" in base


def test_validator_completeness_metrics_are_planned_measurements() -> None:
    text = read_doc()
    metrics = section(text, "## 1. Validator Completeness Metrics", "## 2. Adversarial Mutation and Replay Harness")

    assert "Status: [Planned]" in metrics
    assert "measure coverage," in metrics
    assert "not just pass/fail" in metrics
    for item in VALIDATOR_METRICS:
        assert item in metrics
    assert "This does not prove validator completeness." in metrics


def test_adversarial_harness_is_planned_and_non_exhaustive() -> None:
    text = read_doc()
    harness = section(text, "## 2. Adversarial Mutation and Replay Harness", "## 3. Final CI Collapse")

    assert "Status: [Planned]" in harness
    for item in ADVERSARIAL_ATTEMPTS:
        assert item in harness
    assert "This does not prove universal attack resistance." in harness
    assert "hostile evidence pressure" in harness


def test_final_ci_collapse_remains_planned_until_redundancy_removed() -> None:
    text = read_doc()
    ci = section(text, "## 3. Final CI Collapse", "## Completion Criteria")

    assert "Status: [Planned / In Development]" in ci
    assert "python3 -m afritech.ci.constitutional_pipeline" in ci
    for item in CI_COLLAPSE_PROPERTIES:
        assert item in ci
    assert "afritech/ci/CI_AUTHORITY.yaml" in ci
    assert "Final CI collapse is not claimed complete" in ci


def test_evidence_hardening_roadmap_preserves_boundary_and_avoids_inflation() -> None:
    text = read_doc()

    assert "does not modify `afritech.demo.proof`" in text
    assert "does not expand proof scope beyond the bounded AfriRide domain" in text
    assert "does not claim global deployment readiness" in text
    assert "universal validator completeness" in text
    assert "exhaustive adversarial resistance" in text
    assert "completed final CI collapse" in text
    assert "No new truth." in text
    assert "Only tighter evidence." in text

    lowered = text.lower()
    for claim in FORBIDDEN_INFLATION:
        assert claim not in lowered
