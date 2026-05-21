from __future__ import annotations

from pathlib import Path


DOC = Path(__file__).resolve().parents[3] / "docs/vision/Nova_Ecosystem_Naming_Strategy.md"

REQUIRED_HEADER_LINES = (
    "STATUS: STRATEGIC BRAND POSITIONING SURFACE",
    "CLASSIFICATION: NON-AUTHORITATIVE NAMING STRATEGY",
    "GOVERNANCE MODE: PRESERVE OR ISOLATE",
)

NON_REDEFINED_SURFACES = (
    "constitutional truth",
    "runtime authority",
    "replay authority",
    "execution legality",
    "core invariants",
    "module-path identity",
    "claim admissibility",
    "operational deployment proof",
)

PROPOSED_RENAMES = (
    ("AfriTech", "NovaTech / NovaCore / Nova Continuum"),
    ("AfriRide", "NovaRide"),
    ("AfriPay", "NovaPay"),
    ("AfriID", "NovaID"),
    ("AfriHealth", "NovaHealth"),
    ("AfriCloud", "NovaCloud"),
    ("AfriAI", "NovaAI"),
    ("AfriConnect", "NovaConnect"),
    ("AfriTrust", "NovaTrust"),
    ("AfriLearn", "NovaLearn"),
    ("AfriTalent", "NovaTalent"),
    ("AfriLife OS", "NovaLife OS"),
    ("AfriVirtualMall", "NovaVirtualMall"),
    ("AfriStream", "NovaStream"),
    ("AfriPlay", "NovaPlay"),
    ("AfriNews", "NovaNews"),
    ("AfriHome", "NovaHome"),
    ("AfriAgro", "NovaAgro"),
    ("AfriWork", "NovaWork"),
    ("AfriCivic", "NovaCivic"),
)

FORBIDDEN_INFLATION = (
    "canonical repository identity: nova",
    "runtime/module identity: nova",
    "proof/replay identity: nova",
    "nova migration is complete",
    "afritech is renamed to novatech",
    "afriride is renamed to novaride",
    "brand repositioning proves global readiness",
)


def read_doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_nova_strategy_has_bounded_non_authoritative_classification() -> None:
    text = read_doc()
    lowered = text.lower()

    for line in REQUIRED_HEADER_LINES:
        assert line in text

    assert "does not rename canonical modules" in lowered
    assert "does not redefine" in lowered

    for surface in NON_REDEFINED_SURFACES:
        assert surface in text

    for phrase in FORBIDDEN_INFLATION:
        assert phrase not in lowered


def test_nova_strategy_preserves_positioning_thesis() -> None:
    text = read_doc()

    assert "regional and continental" in text
    assert "next-generation, future-oriented, and globally scalable" in text
    assert "This is a positioning shift, not an execution claim." in text

    for value in (
        "emergence",
        "new systems",
        "transformation",
        "next-generation infrastructure",
        "technological evolution",
        "future-facing scalability",
    ):
        assert value in text

    for domain in (
        "mobility",
        "AI",
        "cloud",
        "finance",
        "health",
        "logistics",
        "identity",
        "infrastructure",
    ):
        assert domain in text


def test_nova_strategy_contains_complete_rename_map() -> None:
    text = read_doc()

    for current, proposed in PROPOSED_RENAMES:
        assert current in text
        assert proposed in text

    for non_identity in (
        "canonical module identities",
        "runtime import paths",
        "proof identities",
        "replay identities",
        "implementation registry entries",
        "authority registry entries",
    ):
        assert non_identity in text


def test_nova_strategy_covers_core_name_variants() -> None:
    text = read_doc()

    for variant in (
        "NovaTech",
        "NovaCore",
        "Nova Continuum",
        "Nova Systems",
        "NovaOS",
    ):
        assert variant in text

    assert "next-generation technology ecosystem" in text
    assert "constitutional foundation" in text
    assert "continuity-preserving digital infrastructure" in text
    assert "enterprise delivery" in text
    assert "operating-system-level evidence" in text


def test_nova_strategy_defines_recommended_architecture() -> None:
    text = read_doc()

    for row in (
        "| Core architecture | NovaCore |",
        "| Ecosystem umbrella | NovaTech |",
        "| Mobility | NovaRide |",
        "| Finance | NovaPay |",
        "| Identity | NovaID |",
        "| Intelligence | NovaAI |",
        "| Cloud | NovaCloud |",
    ):
        assert row in text

    assert "NovaCore - Constitutional Infrastructure for Continuity-Preserving Digital Systems" in text
    assert "NovaTech - Replay-Governed Infrastructure for the Next Generation" in text


def test_nova_strategy_requires_formal_migration_controls() -> None:
    text = read_doc()

    assert "must not be performed as ad hoc search-and-replace" in text

    for control in (
        "path ontology update",
        "canonical module identity review",
        "alias compatibility policy",
        "implementation registry update",
        "surface authority registry update",
        "surface implementation binding update",
        "claim-evidence binding update",
        "documentation redirect map",
        "test migration plan",
        "deprecation timeline",
        "rollback plan",
    ):
        assert control in text


def test_nova_strategy_preserves_constitutional_identity_constraints() -> None:
    text = read_doc()

    for preserved in (
        "replay admissibility",
        "deterministic identity",
        "closed-world execution",
        "path ontology integrity",
        "claim discipline",
        "proof authority boundaries",
    ):
        assert preserved in text

    for forbidden in (
        "silently mutate canonical module paths",
        "treat brand aliases as runtime identity",
        "break replay reconstruction",
        "create undeclared execution surfaces",
        "replace proof authority with naming strategy",
        "claim global readiness from brand repositioning",
    ):
        assert forbidden in text


def test_nova_strategy_preserves_safe_near_term_posture() -> None:
    text = read_doc()

    for posture in (
        "Brand exploration: NovaTech / NovaCore",
        "Canonical repository identity: unchanged",
        "Runtime/module identity: unchanged",
        "Proof/replay identity: unchanged",
        "Documentation status: non-authoritative",
    ):
        assert posture in text

    assert "does not rename AfriTech, AfriRide" in text
    assert "Any future Nova migration requires explicit governance" in text
