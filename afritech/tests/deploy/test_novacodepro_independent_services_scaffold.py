from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_novacodepro_independent_services_scaffold_exists() -> None:
    compose = (ROOT / "deploy/novacodepro/docker-compose.independent-services.yml").read_text()
    k8s = (ROOT / "deploy/novacodepro/kubernetes/novacodepro.yaml").read_text()

    assert "novacodepro-agent" in compose
    assert "novacodepro-agent-worker" in compose
    assert "novacodepro-identity-context" in compose
    assert "novacodepro-command-center" in compose
    assert "redpanda" in compose
    assert "gateway_app" in compose
    assert "Namespace" in k8s
    assert "novacodepro-gateway" in k8s
    assert "novacodepro-agent-worker" in k8s
    assert "novacodepro-identity-context" in k8s
    assert "novacodepro-command-center" in k8s
    assert "redpanda" in k8s
    assert "Replicate the same deployment pattern" not in k8s
