from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]

REQUIRED_NOVASCRIPT_DOCS = [
    "docs/NOVASCRIPT_INDEX.md",
    "docs/NOVASCRIPT_OVERVIEW.md",
    "docs/quickstart/NOVASCRIPT_QUICKSTART.md",
    "docs/ecosystem/NOVASCRIPT_ECOSYSTEM_MAP.md",
    "docs/architecture/NOVASCRIPT_LIFECYCLE.md",
    "docs/standards/NTS_v1.md",
    "docs/sdk/NOVASCRIPT_SDK_GUIDE.md",
    "docs/federation/NOVASCRIPT_FEDERATION_GUIDE.md",
    "docs/portal/NOVASCRIPT_PUBLIC_TRUST_PORTAL.md",
    "docs/certification/NOVASCRIPT_CERTIFICATION_PROGRAM.md",
    "docs/adoption/NOVASCRIPT_ADOPTION_GUIDE.md",
    "docs/governance/NOVASCRIPT_GOVERNANCE_HANDBOOK.md",
    "docs/architecture/NOVASCRIPT_ARCHITECTURE_OBSERVATORY.md",
    "docs/positioning/NOVASCRIPT_EXECUTIVE_ONE_PAGER.md",
    "docs/pitch/NOVASCRIPT_INVESTOR_PARTNER_DECK.md",
    "docs/whitepaper/NOVASCRIPT_TRUST_FRAMEWORK_ISO_DRAFT.md",
]

REQUIRED_NOVASCRIPT_SITE_FILES = [
    "novascript-site/package.json",
    "novascript-site/index.html",
    "novascript-site/src/main.jsx",
    "novascript-site/src/App.jsx",
    "novascript-site/src/styles.css",
]


def test_novascript_documentation_system_files_exist() -> None:
    for relative_path in REQUIRED_NOVASCRIPT_DOCS:
        assert (ROOT / relative_path).exists(), relative_path
    for relative_path in REQUIRED_NOVASCRIPT_SITE_FILES:
        assert (ROOT / relative_path).exists(), relative_path


def test_novascript_index_links_core_documentation_system() -> None:
    text = (ROOT / "docs/NOVASCRIPT_INDEX.md").read_text(encoding="utf-8")

    for required in (
        "NovaScript Overview",
        "Quickstart",
        "Ecosystem Map",
        "NovaScript Trust Specification v1",
        "NovaScript SDK Guide",
        "Public Trust Portal Guide",
        "Certification Program",
        "Adoption Guide",
        "Governance Handbook",
        "Investor and Partner Deck",
        "ISO-style Trust Framework Whitepaper",
        "NovaScript React Site Source",
    ):
        assert required in text


def test_nts_v1_contains_implementation_examples() -> None:
    text = (ROOT / "docs/standards/NTS_v1.md").read_text(encoding="utf-8")

    for required in (
        "Example Governance Receipt",
        "Example Certificate Chain",
        "Example Assurance Report",
        "Example Portable Package",
        "Example Trust Exchange",
        "POST /v1/novascript/validate/artifact",
    ):
        assert required in text


def test_quickstart_and_ecosystem_map_define_adoption_path() -> None:
    quickstart = (ROOT / "docs/quickstart/NOVASCRIPT_QUICKSTART.md").read_text(encoding="utf-8")
    ecosystem = (ROOT / "docs/ecosystem/NOVASCRIPT_ECOSYSTEM_MAP.md").read_text(encoding="utf-8")

    for required in (
        "Generate Artifact",
        "Issue Receipt",
        "Verify Receipt",
        "Validate Artifact",
        "Publish Trust Proof",
    ):
        assert required in quickstart

    for required in (
        "SDK",
        "API",
        "Policy Registry",
        "Certificate Authority",
        "Assurance Engine",
        "Federation",
        "Public Trust Portal",
        "Trust Network",
    ):
        assert required in ecosystem


def test_launch_assets_define_market_regulatory_and_site_surfaces() -> None:
    site = (ROOT / "novascript-site/src/App.jsx").read_text(encoding="utf-8")
    deck = (ROOT / "docs/pitch/NOVASCRIPT_INVESTOR_PARTNER_DECK.md").read_text(encoding="utf-8")
    whitepaper = (ROOT / "docs/whitepaper/NOVASCRIPT_TRUST_FRAMEWORK_ISO_DRAFT.md").read_text(encoding="utf-8")

    for required in (
        "The Trust Layer for AI-Generated Software",
        "Trust Network",
        "Certification",
        "Verify",
    ):
        assert required in site

    for required in (
        "Market Gap",
        "Business Model",
        "Moat",
        "STANDARD -> PLATFORM -> GLOBAL TRUST NETWORK",
    ):
        assert required in deck

    for required in (
        "Scope",
        "Control Framework",
        "Federation Model",
        "Limitations",
        "Future Standardization",
    ):
        assert required in whitepaper


def test_novascript_docs_preserve_boundary_language() -> None:
    combined = "\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in REQUIRED_NOVASCRIPT_DOCS
    ).lower()

    assert "does not grant production authority" in combined
    assert "does not replace legal" in combined
    assert "read-only" in combined
