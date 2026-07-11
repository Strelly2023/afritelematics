from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "novacodepro_portal" / "src" / "App.jsx"
PACKAGE = ROOT / "novacodepro_portal" / "package.json"


def test_novacodepro_portal_is_a_separate_vite_app() -> None:
    package_text = PACKAGE.read_text(encoding="utf-8")
    assert '"name": "novacodepro-portal"' in package_text
    assert '"build": "vite build"' in package_text
    assert '"dev": "vite --host 127.0.0.1"' in package_text


def test_novacodepro_portal_covers_the_expected_workspaces() -> None:
    text = APP.read_text(encoding="utf-8")
    for token in [
        "NovaCodePro",
        "Platform Administrator",
        "Software Engineer",
        "Operations Manager",
        "Business Administrator",
        "Partner Administrator",
        "Customer Success",
        "Executive",
        "Command palette",
        "Multi-window dock",
        "NovaID",
        "Trust Center",
        "Release Center",
        "Observability Center",
        "Data Center",
        "Security Center",
        "Executive Center",
        "Workflow builder",
        "Digital twin",
        "Marketplace",
    ]:
        assert token in text


def test_novacodepro_portal_mentions_the_separate_dashboard_boundary() -> None:
    text = APP.read_text(encoding="utf-8")
    assert "Separate from the current NovaTech dashboard surface." in text
