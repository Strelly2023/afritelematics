from __future__ import annotations

import asyncio
import subprocess

from afritech.platform_runtime.adapters.docker_compose import DockerComposeDeploymentAdapter


def test_docker_compose_deployment_adapter_validates_and_deploys(monkeypatch) -> None:
    calls = []

    def fake_run(args, cwd=None, capture_output=False, text=False, input=None):
        calls.append((tuple(args), cwd))
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    adapter = DockerComposeDeploymentAdapter(compose_file="deploy/production/docker-compose.trust-node.yml", project_dir=".", service_name="novacodepro-portal")
    assert asyncio.run(adapter.validate())["returncode"] == 0
    assert asyncio.run(adapter.deploy({"revision": "r1"}))["returncode"] == 0
    assert calls[0][0][:2] == ("docker", "compose")

