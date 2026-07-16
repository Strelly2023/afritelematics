"""Worker process adapters."""

from __future__ import annotations

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkerProcessSpec:
    product_code: str
    worker_name: str
    command: tuple[str, ...]
    image: str | None
    environment_refs: tuple[str, ...]
    replicas: int
    concurrency: int
    timeout_seconds: int
    restart_policy: str
    health_endpoint: str | None
    queue: str


class LocalProcessWorkerAdapter:
    name = "local_process"
    kind = "worker"

    async def start(self, spec: WorkerProcessSpec) -> dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            *spec.command,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        return {"mode": "REAL", "pid": proc.pid, "worker_name": spec.worker_name}


class DockerComposeWorkerAdapter:
    name = "docker_compose"
    kind = "worker"

    async def start(self, spec: WorkerProcessSpec) -> dict[str, Any]:
        completed = await asyncio.to_thread(subprocess.run, ["docker", "compose", "up", "-d", "--scale", f"{spec.worker_name}={spec.replicas}", spec.worker_name], capture_output=True, text=True)
        return {"mode": "REAL" if completed.returncode == 0 else "UNAVAILABLE", "stdout": completed.stdout, "stderr": completed.stderr}


class KubernetesWorkerAdapter:
    name = "kubernetes"
    kind = "worker"

    async def start(self, spec: WorkerProcessSpec) -> dict[str, Any]:
        completed = await asyncio.to_thread(subprocess.run, ["kubectl", "apply", "-f", "-"], input=b"", capture_output=True)
        return {"mode": "REAL" if completed.returncode == 0 else "UNAVAILABLE", "returncode": completed.returncode}
