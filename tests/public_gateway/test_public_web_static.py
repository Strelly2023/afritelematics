from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "apps/public-web"


def test_public_web_static_metadata_is_canonical() -> None:
    html = (APP / "index.html").read_text()

    assert "AfriTechnology | Trusted Digital Platforms" in html
    assert 'rel="canonical" href="https://afritechnology.com/"' in html
    assert "AfriRide Operator Dashboard" not in html


def test_public_web_routes_and_contact_states_exist() -> None:
    source = (APP / "src/main.jsx").read_text()

    for route in [
        '"/platform"',
        '"/products"',
        '"/solutions"',
        '"/industries"',
        '"/developers"',
        '"/trust"',
        '"/contact"',
        '"/support"',
        '"/accessibility"',
        '"/search"',
        '"/status"',
        '"/verify"',
        '"/downloads"',
    ]:
        assert route in source
    assert "recoverable" in source
    assert "Your input has been preserved" in source


def test_public_web_robots_blocks_internal_operator_paths() -> None:
    robots = (APP / "public/robots.txt").read_text()

    assert "Disallow: /operator" in robots
    assert "Sitemap: https://afritechnology.com/sitemap.xml" in robots

