from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
ALERTMANAGER = ROOT / "deploy/production/monitoring/alertmanager/alertmanager.yml"


def test_alertmanager_configuration_exists_and_routes_default_alerts() -> None:
    assert ALERTMANAGER.exists()
    text = ALERTMANAGER.read_text(encoding="utf-8")
    for item in ("global:", "route:", "receivers:", "default"):
        assert item in text
