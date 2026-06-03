from __future__ import annotations

from pathlib import Path


DOC = (
    Path(__file__).resolve().parents[3]
    / "docs/roadmap/AfriTech_Wave3_Autonomous_Constitutional_Precedent_Governance_Policy.md"
)

REQUIRED_HEADER_LINES = (
    "STATUS: WAVE 3 CONTROL ARTIFACT",
    "CLASSIFICATION: AUTONOMOUS CONSTITUTIONAL PRECEDENT GOVERNANCE POLICY",
    "ROLE: PREVENT HISTORICAL INTERPRETATION MEMORY, REPEATED GOVERNANCE REVIEWS, AND PRECEDENT-LIKE PATTERNS FROM BECOMING BINDING AUTHORITY WITHOUT EXPLICIT AUTHORITY",
    "BOUNDARY: POLICY ONLY; DOES NOT DEFINE LEGITIMACY, REPLAY TRUTH, OR GOVERNANCE ENFORCEMENT",
)

PRECEDENT_RISK_SURFACES = (
    "Historical Reference vs Binding Authority",
    "Governance Memory Containment",
    "Precedent Lineage Governance",
    "Historical Transparency",
    "Jurisprudence Drift",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_constitutional_precedent_policy_has_bounded_classification() -> None:
    text = read_doc()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "historical governance memory -> repeated interpretation pattern -> self-binding jurisprudence" in text
    assert "Precedent memory may improve human understanding of governance history." in text
    assert "Precedent memory must not become constitutional jurisprudence." in text


def test_constitutional_precedent_policy_preserves_authority_stack() -> None:
    text = read_doc()

    for phrase in (
        "Constitution -> legitimacy",
        "Replay -> truth validation",
        "Validators -> governance enforcement",
        "Explanation Schema -> safe explanation units",
        "Composition Schema -> safe narrative aggregation",
        "Cognitive Complexity Budget -> bounded cognition",
        "Salience Policy -> bounded attention semantics",
        "Cross-Surface Consistency Policy -> operational reality coherence across surfaces",
        "Temporal Cognition Consistency Policy -> operational reality coherence across time",
        "Adaptive Cognition Governance Policy -> personalization without truth fragmentation",
        "Collective Adaptive Feedback Governance Policy -> ergonomic feedback without trained truth",
        "Autonomous Optimization Governance Policy -> operational improvement without authority redefinition",
        "Autonomous Objective Evolution Governance Policy -> goal evolution without self-authorized authority",
        "Autonomous Policy Synthesis Governance Policy -> policy proposals without self-ratification",
        "Autonomous Constitutional Interpretation Governance Policy -> ambiguity explanation without legitimacy resolution",
        "Autonomous Constitutional Harmonization Governance Policy -> conflict mapping without supremacy determination",
        "Autonomous Constitutional Precedent Governance Policy -> constitutional memory without jurisprudence formation",
        "Precedent systems -> advisory governance memory only",
        "Operations -> consumption",
    ):
        assert phrase in text

    assert "Autonomous constitutional precedent governance constrains historical reference" in text
    assert "It does not validate truth." in text


def test_constitutional_precedent_policy_declares_risk_surfaces() -> None:
    text = read_doc()

    for risk_surface in PRECEDENT_RISK_SURFACES:
        assert risk_surface in text

    for risk in (
        "Repeated historical references become treated as binding constitutional authority",
        "Governance memory elevates recurrence, popularity, or convergence into authority",
        "Precedent references lose source doctrine, historical review lineage, or ratification status",
        "Historical memory hides the difference between advisory recurrence and binding authority",
        "Repeated autonomous precedent references converge into implied constitutional law",
    ):
        assert risk in text


def test_constitutional_precedent_policy_defines_allowed_and_forbidden_actions() -> None:
    text = read_doc()

    for allowed in (
        "remember historical reviews",
        "compare prior ambiguity",
        "surface recurring disputes",
        "cite governance history",
        "explain historical interpretation patterns",
        "recommend review",
        "trace precedent lineage",
        "classify recurrence",
        "link to source doctrine",
        "distinguish advisory from binding status",
    ):
        assert allowed in text

    for forbidden in (
        "create binding norms",
        "infer jurisprudence",
        "treat repetition as authority",
        "create de facto supremacy",
        "determine future legitimacy",
        "ratify historical interpretation",
        "establish constitutional doctrine from recurrence",
        "weight legitimacy by historical frequency",
        "collapse unresolved ambiguity into precedent",
        "present advisory memory as authority",
    ):
        assert forbidden in text


def test_constitutional_precedent_policy_contains_memory_containment() -> None:
    text = read_doc()

    for memory_signal in (
        "historical frequency",
        "interpretive repetition",
        "review recurrence",
        "past harmonization patterns",
        "governance popularity",
        "historical convergence",
        "repeated operator reliance",
        "citation density",
    ):
        assert memory_signal in text

    assert "into constitutional authority." in text


def test_constitutional_precedent_policy_requires_lineage_and_transparency() -> None:
    text = read_doc()

    for lineage_field in (
        "precedent reference id",
        "precedent reference version",
        "source doctrine references",
        "historical review lineage",
        "ambiguity recurrence scope",
        "replay references when applicable",
        "conflict history",
        "uncertainty classification",
        "ratification status",
        "authority disclaimer",
    ):
        assert lineage_field in text

    for transparency_field in (
        "what is historical",
        "what is binding",
        "what is advisory",
        "what is repeated but unresolved",
        "what is precedent-like but non-authoritative",
        "what requires explicit authority",
        "what source doctrine was used",
        "what ratification status applies",
    ):
        assert transparency_field in text


def test_constitutional_precedent_policy_names_drift_detection() -> None:
    text = read_doc()

    for drift in (
        "implied precedent formation",
        "historical authority convergence",
        "repeated ambiguity normalization",
        "jurisprudential compression",
        "de facto supremacy accumulation",
        "historical weighting escalation",
        "recurrence-as-authority drift",
        "precedent citation inflation",
        "ratification status loss",
        "unresolved recurrence disappearance",
    ):
        assert drift in text


def test_constitutional_precedent_policy_defines_future_policy_and_ga_guard() -> None:
    text = read_doc()

    assert "afritech/constitution/evolution/autonomous_constitutional_precedent_policy.yaml" in text
    assert "schema: afritech.autonomous_constitutional_precedent_policy.v1" in text
    assert "python3 -m afritech.ci.autonomous_constitutional_precedent_validator" in text
    assert "This guard validates autonomous constitutional precedent governance." in text
    assert "not validate replay truth or define legitimacy." in text
    assert (
        "Autonomous precedent may reference history.\n"
        "Binding precedent requires authority."
    ) in text
