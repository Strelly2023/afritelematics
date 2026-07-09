from __future__ import annotations

from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[3]
GRAFANA = ROOT / "deploy/production/monitoring/grafana"


def test_grafana_configuration_includes_datasources_and_dashboards() -> None:
    ds = GRAFANA / "provisioning/datasources/datasources.yml"
    dashboards = GRAFANA / "provisioning/dashboards/dashboards.yml"
    assert ds.exists()
    assert dashboards.exists()

    ds_text = ds.read_text(encoding="utf-8")
    assert "Prometheus" in ds_text
    assert "http://prometheus:9090" in ds_text

    dash_text = dashboards.read_text(encoding="utf-8")
    assert "/var/lib/grafana/dashboards" in dash_text

    for name, title in (
        ("platform.json", "Platform Dashboard"),
        ("api.json", "API Dashboard"),
        ("novaride.json", "NovaRide Dashboard"),
        ("novapay.json", "NovaPay Dashboard"),
        ("novaid.json", "NovaID Dashboard"),
    ):
        payload = json.loads((GRAFANA / "dashboards" / name).read_text(encoding="utf-8"))
        assert payload["title"] == title
        assert payload["panels"]
