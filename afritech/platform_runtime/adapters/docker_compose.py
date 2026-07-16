"""Docker Compose deployment adapter."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class DockerComposeDeploymentAdapter:
    compose_file: str
    project_dir: str
    service_name: str
    name: str = "docker_compose"
    kind: str = "deployment"

    async def render(self, environment: str, region: str, product_code: str, product_version: str) -> dict[str, Any]:
        return {"mode": "REAL", "compose_file": self.compose_file, "service": self.service_name, "product_code": product_code, "product_version": product_version, "environment": environment, "region": region}

    async def validate(self) -> dict[str, Any]:
        completed = await asyncio.to_thread(subprocess.run, ["docker", "compose", "-f", self.compose_file, "config"], cwd=self.project_dir, capture_output=True, text=True)
        return {"mode": "REAL" if completed.returncode == 0 else "UNAVAILABLE", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}

    async def deploy(self, revision: dict[str, Any]) -> dict[str, Any]:
        completed = await asyncio.to_thread(subprocess.run, ["docker", "compose", "-f", self.compose_file, "up", "-d", "--no-build", self.service_name], cwd=self.project_dir, capture_output=True, text=True)
        return {"mode": "REAL" if completed.returncode == 0 else "UNAVAILABLE", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr}

