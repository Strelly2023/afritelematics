from __future__ import annotations

from pathlib import Path

from afritech.ci import afriprog_investor_demo_truth_boundary_validator


ROOT = Path(__file__).resolve().parents[3]


def test_investor_demo_assets_exist_and_are_truth_bound() -> None:
    afriprog_investor_demo_truth_boundary_validator.validate()


def test_demo_is_standalone_static_surface() -> None:
    html = (ROOT / "afriprogramming_demo/index.html").read_text(encoding="utf-8")
    app = (ROOT / "afriprogramming_demo/src/app.js").read_text(encoding="utf-8")

    assert "./src/app.js" in html
    assert "Non-authoritative" in app
    assert "controlled-pilot-ready" in app
    assert "not production-proven" in app
